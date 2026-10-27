import re

import allure
import pytest
from playwright.sync_api import expect

from pages import InventoryPage, LoginPage
from utils.data import as_params, load_json

USERS = load_json("users.json")

pytestmark = [pytest.mark.login, allure.feature("Login")]


@pytest.mark.parametrize(
    "username",
    [pytest.param(name, marks=pytest.mark.smoke if name == USERS["default_user"] else ()) for name in USERS["valid_users"]],
)
def test_valid_user_lands_on_products(login_page, username):
    login_page.login(username, USERS["password"])

    inventory = InventoryPage(login_page.page)
    expect(inventory.page).to_have_url(re.compile(r"/inventory\.html$"))
    expect(inventory.title).to_have_text("Products")


@pytest.mark.parametrize("case", as_params(USERS["invalid_logins"]))
def test_invalid_login_shows_error(login_page, case):
    login_page.login(case["username"], case["password"])

    expect(login_page.error).to_have_text(case["error"])
    expect(login_page.login_button).to_be_visible()


def test_logout_returns_to_login_page(inventory_page):
    inventory_page.header.logout()

    login = LoginPage(inventory_page.page)
    expect(login.login_button).to_be_visible()
    expect(login.page).not_to_have_url(re.compile(r"/inventory\.html"))


def test_inventory_is_not_reachable_without_logging_in(page):
    page.goto(InventoryPage.path)

    expect(LoginPage(page).error).to_have_text(
        "Epic sadface: You can only access '/inventory.html' when you are logged in."
    )
