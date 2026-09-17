"""Scenario step 1 - Login."""
import pytest

from config.settings import settings
from pages.login_page import LoginPage
from utils.reporting import step


@pytest.mark.smoke
def test_login_with_valid_credentials(login_page: LoginPage) -> None:
    with step("Open the OrangeHRM login page"):
        login_page.open()

    with step("Log in with valid credentials and verify the Dashboard is displayed"):
        dashboard = login_page.login(settings.username, settings.password)
        dashboard.verify_loaded()

    with step("Log out and verify the login page is shown again"):
        dashboard.logout()
        login_page.verify_loaded()


@pytest.mark.smoke
def test_login_with_invalid_credentials(login_page: LoginPage) -> None:
    with step("Open the OrangeHRM login page"):
        login_page.open()

    with step("Log in with a wrong password and verify the error message"):
        login_page.login_expecting_failure(settings.username, "wrong-password-123")
        login_page.verify_invalid_credentials_error()
