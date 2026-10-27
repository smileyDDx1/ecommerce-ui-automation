import allure
from playwright.sync_api import Page

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.username = page.get_by_test_id("username")
        self.password = page.get_by_test_id("password")
        self.login_button = page.get_by_test_id("login-button")
        self.error = page.get_by_test_id("error")
        self.ready = self.login_button

    @allure.step("Log in as '{username}'")
    def login(self, username: str, password: str) -> None:
        """Submit the form. Callers check where it led, since logins can be meant to fail."""
        self.username.fill(username)
        self.password.fill(password)
        self.login_button.click()
