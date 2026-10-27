import allure
from playwright.sync_api import Page, expect


class Header:
    """Top bar shown on every logged-in page: cart icon, item count and the burger menu."""

    MENU_OPEN_ATTEMPTS = 3
    MENU_STATE_TIMEOUT_MS = 5000

    def __init__(self, page: Page) -> None:
        self.page = page
        self.cart_link = page.get_by_test_id("shopping-cart-link")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")
        self.menu_button = page.get_by_role("button", name="Open Menu")
        self.menu = page.locator(".bm-menu-wrap")  # the side menu has no test id
        self.logout_link = page.get_by_test_id("logout-sidebar-link")

    def open_menu(self) -> None:
        # On a slow page load a click on the burger button is sometimes lost: the click succeeds
        # but the menu never opens. The button toggles, so a blind second click could close a
        # menu that is still opening. The menu's aria-hidden flips as soon as it starts opening,
        # so click again only while it still says closed.
        for _ in range(self.MENU_OPEN_ATTEMPTS):
            self.menu_button.click()
            try:
                expect(self.menu).to_have_attribute("aria-hidden", "false", timeout=self.MENU_STATE_TIMEOUT_MS)
                return
            except AssertionError:
                continue
        raise AssertionError(f"Side menu did not open after {self.MENU_OPEN_ATTEMPTS} clicks")

    @allure.step("Log out from the side menu")
    def logout(self) -> None:
        self.open_menu()
        self.logout_link.click()
