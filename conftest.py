"""Browser lifecycle, cross-browser parametrisation and failure artifacts.

Fixtures, from widest to narrowest scope:
    playwright      one Playwright driver per worker process
    browser         one launched browser per worker and browser type
    login_session   a saved logged-in session per worker and browser type
    page            a fresh, logged-out page in its own context (per test)
    logged_in_page  a fresh page that already holds the standard_user session

Each test context is traced. When a test fails, its screenshot, Playwright trace
and browser console are written to test-results/<test>/ and attached to Allure.
"""

import math
import platform
import re
import shutil
import time
from contextlib import contextmanager
from importlib.metadata import version
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Browser, BrowserContext, Error, Page, expect, sync_playwright

from config import settings
from pages import InventoryPage, LoginPage
from utils.data import load_json

SUPPORTED_BROWSERS = ("chromium", "firefox", "webkit")
BROWSERS_KEY = pytest.StashKey[list]()
PHASE_REPORTS_KEY = pytest.StashKey[dict]()

# Turns off CSS transitions and animations, so elements such as the sliding side menu are in
# their final place as soon as they render. Tests check behaviour, not motion.
NO_ANIMATIONS_SCRIPT = """
document.addEventListener('DOMContentLoaded', () => {
  const style = document.createElement('style');
  style.textContent = '*, *::before, *::after { transition: none !important; animation: none !important; }';
  document.head.appendChild(style);
});
"""


def pytest_addoption(parser):
    group = parser.getgroup("ui", "UI test options")
    group.addoption(
        "--browsers",
        default=settings.BROWSERS,
        help="Comma-separated browsers to run on: chromium, firefox, webkit (env BROWSERS).",
    )
    group.addoption("--base-url", default=settings.BASE_URL, help="Site under test (env BASE_URL).")
    group.addoption(
        "--browser-channel",
        default=None,
        help="Run Chromium tests on an installed branded browser instead: chrome or msedge.",
    )
    group.addoption("--headed", action="store_true", help="Show the browser windows.")
    group.addoption("--slowmo", type=int, default=0, help="Pause N ms after each Playwright action.")


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    browsers = [name.strip().lower() for name in config.getoption("--browsers").split(",") if name.strip()]
    unknown = sorted(set(browsers) - set(SUPPORTED_BROWSERS))
    if not browsers or unknown:
        raise pytest.UsageError(
            f"--browsers got {unknown or 'nothing'}; choose from {', '.join(SUPPORTED_BROWSERS)}"
        )
    config.stash[BROWSERS_KEY] = list(dict.fromkeys(browsers))

    # Start each run without the previous run's failure artifacts.
    if not hasattr(config, "workerinput") and not config.option.collectonly:
        shutil.rmtree(settings.ARTIFACTS_DIR, ignore_errors=True)

    # allure-pytest honours --clean-alluredir in every xdist worker, so a worker that starts late
    # deletes results the others already wrote. Clean once on the controller and switch it off.
    if config.option.clean_alluredir:
        if config.option.allure_report_dir and not hasattr(config, "workerinput") and not config.option.collectonly:
            shutil.rmtree(config.option.allure_report_dir, ignore_errors=True)
        config.option.clean_alluredir = False


def pytest_generate_tests(metafunc):
    # Any test that needs a browser, directly or through other fixtures, runs once per browser.
    if "browser_name" in metafunc.fixturenames:
        metafunc.parametrize("browser_name", metafunc.config.stash[BROWSERS_KEY], scope="session")


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # Keep each phase's report on the test so fixtures can tell, at teardown, whether it failed.
    report = yield
    item.stash.setdefault(PHASE_REPORTS_KEY, {})[report.when] = report
    return report


def pytest_sessionfinish(session):
    """Write Allure's environment panel and failure categories (once, on the controller)."""
    results_dir = session.config.getoption("allure_report_dir", None)
    if not results_dir or hasattr(session.config, "workerinput"):
        return
    results = Path(results_dir)
    results.mkdir(parents=True, exist_ok=True)
    environment = {
        "Base.URL": session.config.getoption("--base-url"),
        "Browsers": ", ".join(session.config.stash[BROWSERS_KEY]),
        "Playwright": version("playwright"),
        "Python": platform.python_version(),
        "OS": f"{platform.system()} {platform.release()}",
    }
    (results / "environment.properties").write_text(
        "".join(f"{key}={value}\n" for key, value in environment.items()), encoding="utf-8"
    )
    shutil.copy(settings.ROOT_DIR / "config" / "allure_categories.json", results / "categories.json")


@pytest.fixture(scope="session")
def base_url(pytestconfig) -> str:
    return pytestconfig.getoption("--base-url").rstrip("/")


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as pw:
        pw.selectors.set_test_id_attribute("data-test")
        expect.set_options(timeout=settings.EXPECT_TIMEOUT_MS)
        yield pw


@pytest.fixture(scope="session")
def browser(playwright, browser_name, pytestconfig) -> Browser:
    launch_args = {
        "headless": not pytestconfig.getoption("--headed"),
        "slow_mo": pytestconfig.getoption("--slowmo"),
    }
    if browser_name == "chromium" and pytestconfig.getoption("--browser-channel"):
        launch_args["channel"] = pytestconfig.getoption("--browser-channel")
    browser = getattr(playwright, browser_name).launch(**launch_args)
    yield browser
    browser.close()


class LoginSession:
    """Logs in through the UI and hands out the saved session until its cookies near expiry.

    saucedemo's login cookie only lasts 10 minutes, so one login per run is not enough.
    """

    REFRESH_MARGIN_S = 60

    def __init__(self, browser: Browser, base_url: str) -> None:
        self._browser = browser
        self._base_url = base_url
        self._state: dict | None = None
        self._expires_at = 0.0

    def storage_state(self) -> dict:
        if self._state is None or time.time() > self._expires_at - self.REFRESH_MARGIN_S:
            self._state = self._log_in()
            expiries = [cookie["expires"] for cookie in self._state["cookies"] if cookie["expires"] > 0]
            self._expires_at = min(expiries, default=math.inf)
        return self._state

    def _log_in(self) -> dict:
        users = load_json("users.json")
        context = _new_context(self._browser, self._base_url)
        try:
            page = context.new_page()
            LoginPage(page).open().login(users["default_user"], users["password"])
            expect(InventoryPage(page).title).to_have_text("Products")
            return context.storage_state()
        finally:
            context.close()


@pytest.fixture(scope="session")
def login_session(browser, base_url) -> LoginSession:
    """One reusable standard_user session per worker and browser."""
    return LoginSession(browser, base_url)


@pytest.fixture
def page(browser, base_url, request) -> Page:
    """A logged-out page in a brand-new browser context."""
    with _traced_page(browser, base_url, request) as page:
        yield page


@pytest.fixture
def logged_in_page(browser, base_url, request, login_session) -> Page:
    """A page in a new context that starts with the saved standard_user session."""
    with _traced_page(browser, base_url, request, storage_state=login_session.storage_state()) as page:
        yield page


def _new_context(browser: Browser, base_url: str, **context_args) -> BrowserContext:
    context = browser.new_context(base_url=base_url, viewport=settings.VIEWPORT, **context_args)
    context.set_default_timeout(settings.ACTION_TIMEOUT_MS)
    context.set_default_navigation_timeout(settings.NAVIGATION_TIMEOUT_MS)
    context.add_init_script(NO_ANIMATIONS_SCRIPT)
    return context


@contextmanager
def _traced_page(browser: Browser, base_url: str, request, **context_args):
    context = _new_context(browser, base_url, **context_args)
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    console: list[str] = []
    page.on("console", lambda msg: console.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda exc: console.append(f"[pageerror] {exc}"))
    try:
        yield page
    finally:
        if _failed(request.node):
            _save_failure_artifacts(request.node, page, context, console)
        else:
            context.tracing.stop()
        context.close()


def _failed(item) -> bool:
    reports = item.stash.get(PHASE_REPORTS_KEY, {})
    return any(report.failed for report in reports.values())


def _save_failure_artifacts(item, page: Page, context: BrowserContext, console: list[str]) -> None:
    out_dir = settings.ARTIFACTS_DIR / re.sub(r"[^\w.-]+", "_", item.nodeid).strip("_")
    out_dir.mkdir(parents=True, exist_ok=True)

    screenshot = out_dir / "screenshot.png"
    try:
        page.screenshot(path=screenshot, full_page=True)
        allure.attach.file(screenshot, name="Screenshot on failure", attachment_type=allure.attachment_type.PNG)
    except Error as exc:  # the page may have crashed or closed
        allure.attach(str(exc), name="Screenshot failed", attachment_type=allure.attachment_type.TEXT)

    trace = out_dir / "trace.zip"
    context.tracing.stop(path=trace)
    allure.attach.file(trace, name="Playwright trace (open with: playwright show-trace)", extension="zip")

    allure.attach(page.url, name="Page URL", attachment_type=allure.attachment_type.URI_LIST)
    if console:
        (out_dir / "console.log").write_text("\n".join(console), encoding="utf-8")
        allure.attach("\n".join(console), name="Browser console", attachment_type=allure.attachment_type.TEXT)
