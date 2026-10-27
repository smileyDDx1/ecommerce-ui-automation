# E-commerce UI automation framework

End-to-end UI tests for the [Sauce Labs demo store](https://www.saucedemo.com), covering the
journeys a shopper takes: logging in, browsing products, managing the cart and checking out.

**Stack:** Python · Playwright · pytest · pytest-xdist · Allure · GitHub Actions

- **Page Object Model.** Each page wraps its locators and actions; tests read as user steps.
- **Fixtures own the browser.** One browser per worker and browser type, a fresh context per test,
  and a logged-in session saved once and reused instead of logging in through the UI every time.
- **Data-driven.** Users, invalid logins, products, sort orders, carts and checkout cases live in
  `data/*.json`; adding a case is a JSON edit, not a code change.
- **Cross-browser and parallel.** Every test runs on Chromium, Firefox and WebKit, spread across
  CPU cores with pytest-xdist.
- **Failure evidence.** A failing test saves a full-page screenshot, a Playwright trace and the
  browser console to `test-results/` and attaches them to its Allure result.

## Layout

```
config/settings.py          base URL, browsers, timeouts (all overridable by env vars)
config/allure_categories.json   how Allure groups failures
data/                       test data: users, products, checkout cases
pages/                      page objects (login, inventory, product, cart, checkout steps)
pages/components/header.py  cart icon and side menu shared by logged-in pages
utils/                      JSON loading, price parsing and order-total maths
conftest.py                 browser fixtures, cross-browser parametrisation, failure artifacts
tests/                      test modules, one per area, plus a full purchase journey
.github/workflows/          CI: every push, pull request, nightly, and on demand
```

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` elsewhere
pip install -r requirements.txt
python -m playwright install chromium firefox webkit
```

## Running

```bash
pytest                                              # Chromium only, one process
pytest -n auto --browsers chromium,firefox,webkit   # all browsers, in parallel
pytest -m smoke                                     # critical path only
pytest -m "cart or checkout" --browsers firefox
pytest tests/test_login.py --headed --slowmo 300    # watch it run
```

| Option | Env var | Default |
| --- | --- | --- |
| `--browsers` | `BROWSERS` | `chromium` |
| `--base-url` | `BASE_URL` | `https://www.saucedemo.com` |
| `--browser-channel` | | none; `chrome` or `msedge` runs the Chromium tests on that installed browser |
| `--headed` | | off |
| `--slowmo N` | | `0` |

Timeouts can be changed with `ACTION_TIMEOUT_MS`, `NAVIGATION_TIMEOUT_MS` and `EXPECT_TIMEOUT_MS`.

Markers: `smoke`, `login`, `inventory`, `cart`, `checkout`, `e2e`.

## Reports and debugging failures

Each run writes fresh results to `allure-results/`. To view them you need the
[Allure CLI](https://allurereport.org/docs/install/) (it requires Java 8+):

```bash
allure serve allure-results
```

A failed test's Allure page has its screenshot, URL, browser console and Playwright trace. The same
files are in `test-results/<test name>/`. Open a trace to step through every action with DOM
snapshots and network calls:

```bash
python -m playwright show-trace test-results/<test name>/trace.zip
```

## CI

`.github/workflows/ui-tests.yml` runs on every push and pull request, nightly at 02:00 UTC, and on
demand (with a choice of browsers and a marker expression). It runs the whole suite on all three
browsers with `pytest -n auto`, uploads the Allure results and any failure artifacts, then builds the
Allure report. On `main` the report is published to GitHub Pages (the `gh-pages` branch) and keeps
its trend history between runs. To see it, enable Pages for the `gh-pages` branch in the
repository settings.

## Notes on the design

- **No pytest-playwright plugin.** The fixtures are written here so the browser lifecycle, tracing
  and artifact handling are explicit. Don't install the plugin alongside: its `page` and `browser`
  fixtures and `--headed` option would clash.
- **Locators** use saucedemo's `data-test` attributes (`get_by_test_id`) or accessible roles, and
  product cards are found by their exact name, so tests don't depend on CSS classes or position.
- **Assertions** use Playwright's `expect`, which retries until the page settles, so there are no
  sleeps. Prices are compared as `Decimal`, and expected totals are worked out from the catalog
  in `data/products.json` with the site's 8% tax.
- **Page readiness.** The store navigates client-side and several pages share test ids (every
  product list uses `inventory-item`). WebKit can report a new URL before the new page renders,
  so each page object names an element only it shows (`self.ready`), and every navigation method
  waits for it before handing back the next page object.
- **Session reuse.** The login cookie expires after 10 minutes, so `LoginSession` logs in again
  shortly before the saved session's cookies expire instead of reusing one login for the whole run.
- **No animations.** Each context injects a stylesheet that turns off CSS transitions and
  animations, so the sliding side menu is usable as soon as it opens.
