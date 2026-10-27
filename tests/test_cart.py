import allure
import pytest
from playwright.sync_api import expect

from utils.data import as_params, load_json
from utils.money import format_amount

CARTS = load_json("checkout.json")["carts"]
BACKPACK = "Sauce Labs Backpack"

pytestmark = [pytest.mark.cart, allure.feature("Cart")]


@pytest.mark.smoke
def test_adding_an_item_updates_badge_and_button(inventory_page):
    inventory_page.add_to_cart(BACKPACK)

    expect(inventory_page.header.cart_badge).to_have_text("1")
    expect(inventory_page.remove_button(BACKPACK)).to_be_visible()


@pytest.mark.parametrize("cart", as_params(CARTS))
def test_cart_lists_added_items_with_prices(inventory_page, prices, cart):
    inventory_page.add_all_to_cart(cart["items"])
    expect(inventory_page.header.cart_badge).to_have_text(str(len(cart["items"])))

    cart_page = inventory_page.open_cart()
    expect(cart_page.title).to_have_text("Your Cart")
    expect(cart_page.item_names).to_have_text(cart["items"])
    expect(cart_page.item_prices).to_have_text([format_amount(prices[name]) for name in cart["items"]])


def test_removing_from_product_list_clears_badge(inventory_page):
    inventory_page.add_to_cart(BACKPACK)
    inventory_page.remove_from_cart(BACKPACK)

    expect(inventory_page.header.cart_badge).to_be_hidden()
    expect(inventory_page.add_button(BACKPACK)).to_be_visible()


def test_removing_from_cart_page_keeps_other_items(inventory_page):
    inventory_page.add_all_to_cart([BACKPACK, "Sauce Labs Onesie"])
    cart_page = inventory_page.open_cart()

    cart_page.remove(BACKPACK)

    expect(cart_page.item_names).to_have_text(["Sauce Labs Onesie"])
    expect(cart_page.header.cart_badge).to_have_text("1")


def test_continue_shopping_keeps_the_cart(inventory_page):
    inventory_page.add_to_cart(BACKPACK)

    inventory = inventory_page.open_cart().continue_shopping()

    expect(inventory.title).to_have_text("Products")
    expect(inventory.header.cart_badge).to_have_text("1")
    expect(inventory.remove_button(BACKPACK)).to_be_visible()


def test_item_added_on_detail_page_shows_in_cart(inventory_page):
    detail = inventory_page.open_product("Sauce Labs Fleece Jacket")
    detail.add_to_cart()
    expect(detail.remove_button).to_be_visible()

    cart_page = detail.back_to_products().open_cart()

    expect(cart_page.item_names).to_have_text(["Sauce Labs Fleece Jacket"])
