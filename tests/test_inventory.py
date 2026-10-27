from decimal import Decimal

import allure
import pytest
from playwright.sync_api import expect

from utils.data import as_params, load_json
from utils.money import format_amount

PRODUCTS = load_json("products.json")

pytestmark = [pytest.mark.inventory, allure.feature("Product browsing")]


def test_catalog_lists_every_product_with_its_price(inventory_page, catalog):
    expect(inventory_page.items).to_have_count(len(catalog))
    expect(inventory_page.item_names).to_have_text([product["name"] for product in catalog])
    expect(inventory_page.item_prices).to_have_text([f"${product['price']}" for product in catalog])


@pytest.mark.parametrize("sort", as_params(PRODUCTS["sort_options"]))
def test_sorting_orders_products(inventory_page, catalog, sort):
    inventory_page.sort_by(sort["value"])

    if sort["field"] == "name":
        expected = sorted((product["name"] for product in catalog), reverse=sort["descending"])
        expect(inventory_page.item_names).to_have_text(expected)
    else:
        # Compare prices only: two products cost the same, so their relative order is not defined.
        amounts = sorted((Decimal(product["price"]) for product in catalog), reverse=sort["descending"])
        expect(inventory_page.item_prices).to_have_text([format_amount(amount) for amount in amounts])


@pytest.mark.parametrize("product", as_params(PRODUCTS["products"]))
def test_product_detail_page_matches_listing(inventory_page, product):
    detail = inventory_page.open_product(product["name"])

    expect(detail.name).to_have_text(product["name"])
    expect(detail.price).to_have_text(f"${product['price']}")
    expect(detail.description).not_to_be_empty()

    inventory = detail.back_to_products()
    expect(inventory.title).to_have_text("Products")
