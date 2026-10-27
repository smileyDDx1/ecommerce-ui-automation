import allure
from playwright.sync_api import Locator, Page

from pages.base_page import StorefrontPage
from pages.product_page import ProductPage


class InventoryPage(StorefrontPage):
    """The product listing ("Products") users land on after logging in."""

    path = "/inventory.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.items = page.get_by_test_id("inventory-item")
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.item_prices = page.get_by_test_id("inventory-item-price")
        self.sort_select = page.get_by_test_id("product-sort-container")
        self.ready = self.sort_select

    def item(self, name: str) -> Locator:
        """The product card whose name is exactly `name`."""
        return self.items.filter(has=self.page.get_by_text(name, exact=True))

    def add_button(self, name: str) -> Locator:
        return self.item(name).get_by_role("button", name="Add to cart")

    def remove_button(self, name: str) -> Locator:
        return self.item(name).get_by_role("button", name="Remove")

    @allure.step("Add '{name}' to the cart")
    def add_to_cart(self, name: str) -> None:
        self.add_button(name).click()

    def add_all_to_cart(self, names: list[str]) -> None:
        for name in names:
            self.add_to_cart(name)

    @allure.step("Remove '{name}' from the cart")
    def remove_from_cart(self, name: str) -> None:
        self.remove_button(name).click()

    @allure.step("Sort products by '{option}'")
    def sort_by(self, option: str) -> None:
        self.sort_select.select_option(option)

    @allure.step("Open the detail page of '{name}'")
    def open_product(self, name: str) -> ProductPage:
        self.item(name).get_by_test_id("inventory-item-name").click()
        return ProductPage(self.page).wait_until_open()
