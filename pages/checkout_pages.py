"""The three checkout steps: customer details, order overview and confirmation."""

from decimal import Decimal

import allure
from playwright.sync_api import Page

from pages.base_page import StorefrontPage
from utils.money import parse_amount


class CheckoutInfoPage(StorefrontPage):
    path = "/checkout-step-one.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.first_name = page.get_by_test_id("firstName")
        self.last_name = page.get_by_test_id("lastName")
        self.postal_code = page.get_by_test_id("postalCode")
        self.continue_button = page.get_by_test_id("continue")
        self.cancel_button = page.get_by_test_id("cancel")
        self.error = page.get_by_test_id("error")
        self.ready = self.continue_button

    @allure.step("Submit customer details: {first_name} {last_name}, {postal_code}")
    def submit(self, first_name: str, last_name: str, postal_code: str) -> None:
        """Fill and submit the form. Use continue_to_overview() when it should succeed."""
        self.first_name.fill(first_name)
        self.last_name.fill(last_name)
        self.postal_code.fill(postal_code)
        self.continue_button.click()

    def continue_to_overview(self, first_name: str, last_name: str, postal_code: str) -> "CheckoutOverviewPage":
        self.submit(first_name, last_name, postal_code)
        return CheckoutOverviewPage(self.page).wait_until_open()

    @allure.step("Cancel checkout")
    def cancel(self):
        from pages.cart_page import CartPage

        self.cancel_button.click()
        return CartPage(self.page).wait_until_open()


class CheckoutOverviewPage(StorefrontPage):
    path = "/checkout-step-two.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.items = page.get_by_test_id("inventory-item")
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.subtotal_label = page.get_by_test_id("subtotal-label")
        self.tax_label = page.get_by_test_id("tax-label")
        self.total_label = page.get_by_test_id("total-label")
        self.finish_button = page.get_by_test_id("finish")
        self.ready = self.finish_button

    def subtotal(self) -> Decimal:
        return parse_amount(self.subtotal_label.inner_text())

    def tax(self) -> Decimal:
        return parse_amount(self.tax_label.inner_text())

    def total(self) -> Decimal:
        return parse_amount(self.total_label.inner_text())

    @allure.step("Finish the order")
    def finish(self) -> "CheckoutCompletePage":
        self.finish_button.click()
        return CheckoutCompletePage(self.page).wait_until_open()


class CheckoutCompletePage(StorefrontPage):
    path = "/checkout-complete.html"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.complete_header = page.get_by_test_id("complete-header")
        self.complete_text = page.get_by_test_id("complete-text")
        self.back_home_button = page.get_by_test_id("back-to-products")
        self.ready = self.complete_header

    @allure.step("Go back to the product list")
    def back_home(self):
        from pages.inventory_page import InventoryPage

        self.back_home_button.click()
        return InventoryPage(self.page).wait_until_open()
