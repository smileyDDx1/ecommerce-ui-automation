import allure
from playwright.sync_api import Page

from pages.base_page import StorefrontPage


class ProductPage(StorefrontPage):
    """Detail page of one product (/inventory-item.html?id=N)."""

    path = "/inventory-item.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.name = page.get_by_test_id("inventory-item-name")
        self.description = page.get_by_test_id("inventory-item-desc")
        self.price = page.get_by_test_id("inventory-item-price")
        self.add_button = page.get_by_role("button", name="Add to cart")
        self.remove_button = page.get_by_role("button", name="Remove")
        self.back_button = page.get_by_test_id("back-to-products")
        self.ready = self.back_button

    @allure.step("Add this product to the cart")
    def add_to_cart(self) -> None:
        self.add_button.click()

    @allure.step("Go back to the product list")
    def back_to_products(self):
        from pages.inventory_page import InventoryPage

        self.back_button.click()
        return InventoryPage(self.page).wait_until_open()
