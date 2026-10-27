import re
from typing import Self

import allure
from playwright.sync_api import Locator, Page

from config import settings
from pages.components.header import Header


class BasePage:
    """A page the tests can open directly. Locators use saucedemo's data-test ids.

    Subclasses set `path` and, in __init__, `self.ready`: an element only that page shows.
    """

    path = "/"
    ready: Locator

    def __init__(self, page: Page) -> None:
        self.page = page

    def open(self) -> Self:
        with allure.step(f"Open {self.path}"):
            # Deep links bounce through a redirect (/inventory.html -> /?/inventory.html -> back),
            # so wait for the page itself rather than for the first document to load.
            self.page.goto(self.path, wait_until="commit")
            return self.wait_until_open()

    def wait_until_open(self) -> Self:
        """Wait until the browser shows this page.

        Navigation in the store is client-side, and WebKit can report the new URL before the
        new page has rendered. Pages share test ids (every product list uses
        "inventory-item"), so the next locator could otherwise match the previous page.
        """
        self.page.wait_for_url(re.compile(re.escape(self.path) + r"(\?|$)"), wait_until="commit")
        self.ready.wait_for(timeout=settings.NAVIGATION_TIMEOUT_MS)
        return self


class StorefrontPage(BasePage):
    """Any page shown after login: it has the header with the cart and the side menu."""

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.header = Header(page)
        self.title = page.get_by_test_id("title")

    def open_cart(self):
        # Imported here because the cart page links back to these pages.
        from pages.cart_page import CartPage

        self.header.cart_link.click()
        return CartPage(self.page).wait_until_open()
