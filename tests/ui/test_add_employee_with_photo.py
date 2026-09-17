"""UI test (screen recorded): create an employee, add the profile photo with the '+' button, save.

Video : reports/videos/test_add_employee_with_profile_photo_<browser>-<data>.webm
        (also embedded in the HTML report and attached to Allure)
Slow  : set SLOW_MO_MS=500 (or pass --slowmo 500) for an easy-to-watch recording
"""
import pytest

from pages.dashboard_page import DashboardPage
from utils.data_models import EmployeeData
from utils.data_reader import load_employees
from utils.image_utils import image_size
from utils.logger import get_logger
from utils.screen_recorder import ScreenRecorder

EMPLOYEES = load_employees()
log = get_logger("test.add_employee_with_photo")


@pytest.mark.smoke
@pytest.mark.parametrize("employee_data", EMPLOYEES, ids=[e.test_id for e in EMPLOYEES])
def test_add_employee_with_profile_photo(
    screen_recorder: ScreenRecorder,
    dashboard: DashboardPage,
    created_employee_ids: list[str],
    employee_data: EmployeeData,
) -> None:
    employee = employee_data.with_unique_identifiers()
    photo = employee.profile_picture
    assert photo is not None, f"Test data '{employee.test_id}' must define profile_picture"
    recorder = screen_recorder

    with recorder.step("1. Logged in - Dashboard is visible"):
        dashboard.verify_loaded()

    with recorder.step("2. Open PIM > Add Employee"):
        add_employee = dashboard.go_to_pim().go_to_add_employee()

    with recorder.step(f"3. Enter name '{employee.display_name}' and Employee Id {employee.employee_id}"):
        add_employee.enter_full_name(employee.first_name, employee.middle_name, employee.last_name)
        add_employee.enter_employee_id(employee.employee_id)

    with recorder.step(f"4. Click '+' and add profile photo '{photo.name}'"):
        add_employee.upload_profile_picture(photo)

    if employee.create_login_details:
        with recorder.step(f"5. Create login details for '{employee.username}'"):
            add_employee.enter_login_details(employee.username, employee.password, employee.login_status)

    with recorder.step("6. Click Save - expect 'Successfully Saved'"):
        personal_details = add_employee.click_save(
            on_saved=lambda: created_employee_ids.append(employee.employee_id)
        )

    with recorder.step("7. Verify the saved employee and the profile photo"):
        personal_details.verify_employee_details(employee)
        personal_details.verify_profile_picture_uploaded()
        personal_details.capture_profile_picture(f"{employee.employee_id}_photo_added")
        shown = personal_details.get_profile_picture_size()
        log.info("Photo '%s' (%sx%s) is shown as %sx%s", photo.name, *image_size(photo), *shown)

    with recorder.step(f"8. Verify employee {employee.employee_id} is listed in Employee List"):
        employee_list = personal_details.go_to_employee_list()
        employee_list.search_by_employee_id(employee.employee_id)
        employee_list.verify_employee_record(employee.employee_id, employee.first_name, employee.last_name)

    recorder.caption(f"Done - employee {employee.employee_id} created with profile photo")
    log.info("Screen recording: %s", recorder.video_file)
