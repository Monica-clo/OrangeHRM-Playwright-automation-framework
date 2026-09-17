"""Extended coverage for the Personal Details and Contact Details tabs (screenshots 3-5)."""
from dataclasses import replace

import pytest

from pages.dashboard_page import DashboardPage
from utils.data_models import random_digits
from utils.data_reader import load_employee_profile
from utils.reporting import step


@pytest.mark.regression
def test_update_personal_and_contact_details(
    dashboard: DashboardPage, created_employee_ids: list[str]
) -> None:
    employee_template, personal_info, contact_info, email_domains = load_employee_profile()
    employee = employee_template.with_unique_identifiers()
    unique = random_digits(6)
    contact_info = replace(
        contact_info,  # work email must be unique in OrangeHRM
        work_email=f"{employee.first_name.lower()}.{unique}@{email_domains['work']}",
        other_email=f"{employee.first_name.lower()}.{unique}@{email_domains['other']}",
    )

    with step(f"Create employee '{employee.employee_id}'"):
        personal_details = dashboard.go_to_pim().go_to_add_employee().add_employee(
            employee, on_saved=lambda: created_employee_ids.append(employee.employee_id)
        )
        personal_details.verify_employee_details(employee)

    with step("Update Personal Details (Other Id, License, Nationality, Marital Status, Gender)"):
        personal_details.update_personal_info(personal_info)

    with step("Reload and verify Personal Details were saved"):
        personal_details.reload()
        personal_details.verify_loaded()
        personal_details.verify_personal_info(personal_info)

    with step("Update Contact Details (Address, Telephone, Email)"):
        contact_details = personal_details.go_to_contact_details()
        contact_details.update_contact_info(contact_info)

    with step("Reload and verify Contact Details were saved"):
        contact_details.reload()
        contact_details.verify_loaded()
        contact_details.verify_contact_info(contact_info)
