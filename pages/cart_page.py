import allure
from playwright.sync_api import Locator, Page

from pages.base_page import StorefrontPage
from pages.checkout_pages import CheckoutInfoPage


class CartPage(StorefrontPage):
    """'Your Cart' page listing what the user has added."""

    path = "/cart.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.items = page.get_by_test_id("inventory-item")
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.item_prices = page.get_by_test_id("inventory-item-price")
        self.checkout_button = page.get_by_test_id("checkout")
        self.continue_shopping_button = page.get_by_test_id("continue-shopping")
        self.ready = self.checkout_button

    def item(self, name: str) -> Locator:
        return self.items.filter(has=self.page.get_by_text(name, exact=True))

    @allure.step("Remove '{name}' from the cart page")
    def remove(self, name: str) -> None:
        self.item(name).get_by_role("button", name="Remove").click()

    @allure.step("Continue shopping")
    def continue_shopping(self):
        from pages.inventory_page import InventoryPage

        self.continue_shopping_button.click()
        return InventoryPage(self.page).wait_until_open()

    @allure.step("Start checkout")
    def checkout(self) -> CheckoutInfoPage:
        self.checkout_button.click()
        return CheckoutInfoPage(self.page).wait_until_open()
