"""Hybrid end-to-end scenario: Employee Lifecycle Management (UI + ReqRes API).

The only APIs used are the ReqRes user APIs:
    POST /api/users, PUT /api/users/{id}, PATCH /api/users/{id}, DELETE /api/users/{id}

1. Login (UI) ............................ dashboard visible
2. Add employee (UI, data-driven) ........ '+' -> add profile photo -> Save -> toast, details, avatar, list
3. Edit employee (UI) .................... change profile photo (avatar really changes)
                                           + Job Title / Employment Status persisted
4. Validate via API (simulated) .......... POST / PUT / PATCH with the UI data -> responses match the UI
5. Delete employee ....................... UI delete + 'No Records Found' + API DELETE -> 204
6. Logout ................................ login page shown, protected page redirects to login
"""
import pytest

from api.base_client import assert_status
from api.models import EmployeeSnapshot, assert_snapshots_match
from api.reqres_client import ReqResClient
from api.schemas import CREATED_USER, UPDATED_USER, assert_schema
from pages.dashboard_page import DashboardPage
from utils.data_models import EmployeeData
from utils.data_reader import load_employees
from utils.image_utils import image_size
from utils.logger import get_logger
from utils.screen_recorder import ScreenRecorder

EMPLOYEES = load_employees()
log = get_logger("test.hybrid")


def assert_echo(body: dict, expected: dict, api_name: str) -> None:
    mismatches = [
        f"  - {field}: UI value {value!r}, API returned {body.get(field)!r}"
        for field, value in expected.items()
        if body.get(field) != value
    ]
    assert not mismatches, f"{api_name} response does not match the UI data:\n" + "\n".join(mismatches)


@pytest.mark.e2e
@pytest.mark.parametrize("employee_data", EMPLOYEES, ids=[e.test_id for e in EMPLOYEES])
def test_employee_lifecycle_ui_and_api(
    screen_recorder: ScreenRecorder,
    dashboard: DashboardPage,
    reqres: ReqResClient,
    created_employee_ids: list[str],
    employee_data: EmployeeData,
) -> None:
    employee = employee_data.with_unique_identifiers()
    assert employee.job is not None, f"Test data '{employee.test_id}' must define job_title and employment_status"

    # ================================================================== 1. LOGIN
    with screen_recorder.step("1. Login - dashboard is visible"):
        dashboard.verify_loaded()

    # ================================================================== 2. ADD EMPLOYEE
    with screen_recorder.step(
        f"2a. PIM > Add Employee '{employee.display_name}' (Employee Id {employee.employee_id}), "
        f"click '+' and add photo '{employee.profile_picture.name if employee.profile_picture else 'none'}', then Save"
    ):
        add_employee_page = dashboard.go_to_pim().go_to_add_employee()
        personal_details = add_employee_page.add_employee(
            employee, on_saved=lambda: created_employee_ids.append(employee.employee_id)
        )
        emp_number = int(personal_details.emp_number)

    with screen_recorder.step("2b. Verify saved details and the added profile photo"):
        personal_details.verify_employee_details(employee)
        if employee.profile_picture:
            personal_details.verify_profile_picture_uploaded()
            personal_details.capture_profile_picture(f"{employee.employee_id}_photo_added")
            log.info("Profile photo added: %s shown as %sx%s (file %sx%s)", employee.profile_picture.name,
                     *personal_details.get_profile_picture_size(), *image_size(employee.profile_picture))

    with screen_recorder.step("2c. Verify the new record is listed in PIM > Employee List"):
        employee_list = personal_details.go_to_employee_list()
        employee_list.search_by_employee_id(employee.employee_id)
        employee_list.verify_employee_record(employee.employee_id, employee.first_name, employee.last_name)

    # ================================================================== 3. EDIT EMPLOYEE
    with screen_recorder.step("3a. Search by Employee Id and open the record"):
        personal_details = employee_list.open_employee_record(employee.employee_id)
        personal_details.verify_employee_details(employee)

    if employee.edit_profile_picture:
        with screen_recorder.step(f"3b. Edit profile photo -> upload '{employee.edit_profile_picture.name}'"):
            photo_before = personal_details.capture_profile_picture(f"{employee.employee_id}_photo_before")
            size_before = personal_details.get_profile_picture_size()
            change_photo_page = personal_details.open_change_profile_picture()
            change_photo_page.change_photo(employee.edit_profile_picture)

        with screen_recorder.step("3c. Verify the new profile photo is shown on Personal Details"):
            personal_details = change_photo_page.go_to_personal_details()
            personal_details.verify_profile_picture_uploaded()
            photo_after = personal_details.capture_profile_picture(f"{employee.employee_id}_photo_after")
            size_after = personal_details.get_profile_picture_size()
            expected_size = image_size(employee.edit_profile_picture)
            assert photo_after != photo_before, (
                "Profile photo did not change: the avatar looks identical before and after the upload"
            )
            assert size_after != size_before, (
                f"Profile photo size should change from {size_before} after the upload, but it is still {size_after}"
            )
            log.info(
                "Profile photo changed: %sx%s -> %sx%s (uploaded file is %sx%s)",
                *size_before, *size_after, *expected_size,
            )

    with screen_recorder.step(f"3d. Update Job Title='{employee.job.job_title}', Status='{employee.job.employment_status}'"):
        job_details = personal_details.go_to_job_details()
        job_details.update_job_details(employee.job)

    with screen_recorder.step("3e. Reload and verify the values were persisted"):
        job_details.reload_and_verify_job_details(employee.job)

    with screen_recorder.step("3f. Verify the updated values in the Employee List"):
        employee_list = job_details.go_to_employee_list()
        employee_list.search_by_employee_id(employee.employee_id)
        employee_list.verify_employee_record(
            employee.employee_id,
            employee.first_name,
            employee.last_name,
            job_title=employee.job.job_title,
            employment_status=employee.job.employment_status,
        )

    # ================================================================== 4. VALIDATE VIA API
    with screen_recorder.step("4a. Read the employee from the UI and check it against the test data"):
        ui = employee_list.get_employee_snapshot(employee.employee_id, emp_number)
        expected = EmployeeSnapshot(
            employee_id=employee.employee_id,
            first_name=employee.first_name,
            middle_name=employee.middle_name,
            last_name=employee.last_name,
            job_title=employee.job.job_title,
            employment_status=employee.job.employment_status,
        )
        assert_snapshots_match(ui, expected, "Employee List (UI) vs test data")

    with screen_recorder.step("4b. POST /api/users with the UI data -> 201 and same name/job"):
        created_payload = {"name": ui.full_name, "job": ui.job_title}
        response = reqres.create_user(created_payload["name"], created_payload["job"])
        assert_status(response, 201)
        created = response.json()
        assert_schema(created, CREATED_USER, "created user")
        assert_echo(created, created_payload, "POST /api/users")
        api_user_id = created["id"]

    with screen_recorder.step(f"4c. PUT /api/users/{api_user_id} with the UI data -> 200 and same name/job"):
        put_payload = {"name": ui.full_name, "job": f"{ui.job_title} - {ui.employee_id}"}
        response = reqres.update_user(api_user_id, put_payload["name"], put_payload["job"])
        assert_status(response, 200)
        updated = response.json()
        assert_schema(updated, UPDATED_USER, "updated user")
        assert_echo(updated, put_payload, "PUT /api/users")

    with screen_recorder.step(f"4d. PATCH /api/users/{api_user_id} with the Employment Status -> 200"):
        patch_payload = {"job": ui.employment_status}
        response = reqres.patch_user(api_user_id, patch_payload)
        assert_status(response, 200)
        patched = response.json()
        assert_schema(patched, UPDATED_USER, "patched user")
        assert_echo(patched, patch_payload, "PATCH /api/users")

    # ================================================================== 5. DELETE EMPLOYEE
    with screen_recorder.step("5a. Delete the employee from the UI"):
        employee_list.delete_employee(employee.employee_id)

    with screen_recorder.step("5b. Verify deletion in the UI (search returns 'No Records Found')"):
        employee_list = employee_list.go_to_employee_list()
        employee_list.verify_employee_not_found(employee.employee_id)
        created_employee_ids.remove(employee.employee_id)  # nothing left to clean up

    with screen_recorder.step(f"5c. DELETE /api/users/{api_user_id} -> 204 with empty body"):
        response = reqres.delete_user(api_user_id)
        assert_status(response, 204)
        assert response.text.strip() == "", f"DELETE should return no body, got {response.text!r}"

    # ================================================================== 6. LOGOUT
    with screen_recorder.step("6a. Logout from the UI"):
        login_page = employee_list.logout()

    with screen_recorder.step("6b. Verify the session is invalidated (protected page redirects to login)"):
        login_page.verify_protected_page_redirects_to_login()
