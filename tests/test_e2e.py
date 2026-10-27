import allure
import pytest
from playwright.sync_api import expect

from pages import InventoryPage
from utils.data import load_json
from utils.money import order_totals

USERS = load_json("users.json")
CUSTOMER = load_json("checkout.json")["customers"][0]

pytestmark = [pytest.mark.e2e, allure.feature("End-to-end journeys")]


@pytest.mark.smoke
def test_shopper_buys_the_two_most_expensive_products(login_page, prices, tax_rate):
    """Log in, sort by price, buy the top two products, pay, then log out."""
    top_two = sorted(prices, key=prices.get, reverse=True)[:2]

    with allure.step("Log in and sort products by price, high to low"):
        login_page.login(USERS["default_user"], USERS["password"])
        inventory = InventoryPage(login_page.page)
        inventory.sort_by("hilo")
        expect(inventory.item_names.nth(0)).to_have_text(top_two[0])
        expect(inventory.item_names.nth(1)).to_have_text(top_two[1])

    with allure.step("Add them to the cart and review it"):
        inventory.add_all_to_cart(top_two)
        cart_page = inventory.open_cart()
        expect(cart_page.item_names).to_have_text(top_two)

    with allure.step("Check out and verify the order total"):
        overview = cart_page.checkout().continue_to_overview(
            CUSTOMER["first_name"], CUSTOMER["last_name"], CUSTOMER["postal_code"]
        )
        _, _, total = order_totals((prices[name] for name in top_two), tax_rate)
        assert overview.total() == total

    with allure.step("Finish the order and log out"):
        complete = overview.finish()
        expect(complete.complete_header).to_have_text("Thank you for your order!")
        complete.header.logout()
        expect(login_page.login_button).to_be_visible()
