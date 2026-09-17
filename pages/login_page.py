"""Login page object."""
from __future__ import annotations

import re

from playwright.sync_api import Page, expect

from config.settings import settings
from locators.common_locators import Messages
from locators.login_locators import LoginLocators as L
from pages.base_page import BasePage
from pages.dashboard_page import DashboardPage


class LoginPage(BasePage):
    URL_PATTERN = re.compile(r"/auth/login")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username_input = page.locator(L.USERNAME_INPUT)
        self.password_input = page.locator(L.PASSWORD_INPUT)
        self.login_button = page.locator(L.LOGIN_BUTTON)
        self.invalid_credentials_alert = page.locator(L.INVALID_CREDENTIALS_ALERT)
        self.login_title = page.locator(L.LOGIN_TITLE)

    def open(self) -> "LoginPage":
        self.navigate(settings.login_path)
        self.verify_loaded()
        return self

    def verify_loaded(self) -> "LoginPage":
        expect(self.page, "Login page URL should be opened").to_have_url(self.URL_PATTERN)
        expect(self.username_input, "Username field should be visible on the login page").to_be_visible()
        expect(self.login_button, "Login button should be visible on the login page").to_be_visible()
        return self

    def enter_credentials(self, username: str, password: str) -> None:
        self.fill(self.username_input, username, "Username")
        self.fill(self.password_input, password, "Password", secret=True)

    def login(self, username: str, password: str) -> DashboardPage:
        """Log in with valid credentials and return the Dashboard page."""
        self.enter_credentials(username, password)
        self.click(self.login_button, "Login button")
        dashboard = DashboardPage(self.page)
        dashboard.verify_loaded()
        return dashboard

    def login_expecting_failure(self, username: str, password: str) -> "LoginPage":
        self.enter_credentials(username, password)
        self.click(self.login_button, "Login button")
        return self

    def verify_protected_page_redirects_to_login(self) -> None:
        """After logout, opening the dashboard URL directly must bounce back to login."""
        self.log.info("Opening protected page %s without a session", settings.dashboard_path)
        self.page.goto(f"{settings.base_url}{settings.dashboard_path}", wait_until="domcontentloaded")
        expect(
            self.page, "Protected page should redirect to login when the session is invalidated"
        ).to_have_url(self.URL_PATTERN)
        expect(self.login_button, "Login form should be displayed again").to_be_visible()

    def verify_invalid_credentials_error(self) -> None:
        expect(
            self.invalid_credentials_alert,
            f"Error '{Messages.INVALID_CREDENTIALS}' should be shown for wrong credentials",
        ).to_have_text(Messages.INVALID_CREDENTIALS)
        expect(self.page, "User should stay on the login page").to_have_url(self.URL_PATTERN)
