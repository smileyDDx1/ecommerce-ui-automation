import re

import allure
import pytest
from playwright.sync_api import expect

from utils.data import as_params, load_json
from utils.money import order_totals

CHECKOUT = load_json("checkout.json")
CUSTOMER = CHECKOUT["customers"][0]

pytestmark = [pytest.mark.checkout, allure.feature("Checkout")]


def _customer_fields(customer: dict) -> dict:
    return {key: customer[key] for key in ("first_name", "last_name", "postal_code")}


@pytest.fixture
def checkout_info(inventory_page):
    """Checkout step one with the backpack in the cart."""
    inventory_page.add_to_cart("Sauce Labs Backpack")
    return inventory_page.open_cart().checkout()


@pytest.mark.parametrize("case", as_params(CHECKOUT["missing_field_cases"]))
def test_customer_details_are_required(checkout_info, case):
    checkout_info.submit(**case["customer"])

    expect(checkout_info.error).to_have_text(case["error"])
    expect(checkout_info.page).to_have_url(re.compile(r"/checkout-step-one\.html$"))


@pytest.mark.parametrize("cart", as_params(CHECKOUT["carts"]))
def test_overview_shows_correct_totals(inventory_page, prices, tax_rate, cart):
    inventory_page.add_all_to_cart(cart["items"])
    overview = inventory_page.open_cart().checkout().continue_to_overview(**_customer_fields(CUSTOMER))

    expect(overview.item_names).to_have_text(cart["items"])
    subtotal, tax, total = order_totals((prices[name] for name in cart["items"]), tax_rate)
    assert overview.subtotal() == subtotal
    assert overview.tax() == tax
    assert overview.total() == total


def test_cancel_on_details_step_returns_to_cart(checkout_info):
    cart_page = checkout_info.cancel()

    expect(cart_page.title).to_have_text("Your Cart")
    expect(cart_page.item_names).to_have_text(["Sauce Labs Backpack"])


@pytest.mark.smoke
@pytest.mark.parametrize("customer", as_params(CHECKOUT["customers"]))
def test_completed_order_empties_the_cart(checkout_info, customer):
    complete = checkout_info.continue_to_overview(**_customer_fields(customer)).finish()

    expect(complete.title).to_have_text("Checkout: Complete!")
    expect(complete.complete_header).to_have_text("Thank you for your order!")
    expect(complete.header.cart_badge).to_be_hidden()

    inventory = complete.back_home()
    expect(inventory.title).to_have_text("Products")
