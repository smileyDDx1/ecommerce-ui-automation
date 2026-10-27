"""Run-time settings. Every value can be overridden with an environment variable."""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", ROOT_DIR / "test-results"))

BASE_URL = os.getenv("BASE_URL", "https://www.saucedemo.com")
BROWSERS = os.getenv("BROWSERS", "chromium")

# Playwright timeouts, in milliseconds.
ACTION_TIMEOUT_MS = int(os.getenv("ACTION_TIMEOUT_MS", "15000"))
NAVIGATION_TIMEOUT_MS = int(os.getenv("NAVIGATION_TIMEOUT_MS", "30000"))
EXPECT_TIMEOUT_MS = int(os.getenv("EXPECT_TIMEOUT_MS", "10000"))

VIEWPORT = {"width": 1366, "height": 768}
