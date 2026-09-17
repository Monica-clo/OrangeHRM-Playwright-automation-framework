"""Dashboard page object (landing page after login)."""
from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from locators.common_locators import SideMenu
from locators.login_locators import DashboardLocators as L
from pages.base_page import BasePage


class DashboardPage(BasePage):
    URL_PATTERN = re.compile(r"/dashboard/index")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.widgets = page.locator(L.DASHBOARD_WIDGETS)

    def verify_loaded(self) -> "DashboardPage":
        expect(self.page, "User should be redirected to the Dashboard after login").to_have_url(self.URL_PATTERN)
        self.verify_module_header(L.DASHBOARD_HEADER_TEXT)
        expect(self.user_dropdown, "Logged-in user profile menu should be visible").to_be_visible()
        self.log.info("Logged in as '%s'", self.user_dropdown_name.inner_text().strip())
        return self

    def go_to_pim(self):
        from pages.employee_list_page import EmployeeListPage

        self.open_side_menu(SideMenu.PIM)
        employee_list = EmployeeListPage(self.page)
        employee_list.verify_loaded()
        return employee_list
