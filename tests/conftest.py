"""Page-object fixtures shared by the test modules."""

from decimal import Decimal

import pytest

from pages import InventoryPage, LoginPage
from utils.data import load_json


@pytest.fixture
def login_page(page) -> LoginPage:
    return LoginPage(page).open()


@pytest.fixture
def inventory_page(logged_in_page) -> InventoryPage:
    return InventoryPage(logged_in_page).open()


@pytest.fixture(scope="session")
def catalog() -> list[dict]:
    return load_json("products.json")["products"]


@pytest.fixture(scope="session")
def prices(catalog) -> dict[str, Decimal]:
    """Expected price of each product, by name."""
    return {product["name"]: Decimal(product["price"]) for product in catalog}


@pytest.fixture(scope="session")
def tax_rate() -> Decimal:
    return Decimal(load_json("products.json")["tax_rate"])
