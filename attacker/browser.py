import ipaddress
import time
from urllib.parse import urlsplit, urlunsplit

from playwright.sync_api import Error as PlaywrightError, Page, Route

from settings import (
    ATTACKER_PASSWORD,
    ATTACKER_USERNAME,
)
from logs import emit  # type: ignore


def origin(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("TARGET_URL must be an absolute http(s) URL")

    hostname = parsed.hostname or ""
    local_names = {"localhost", "web", "host.docker.internal"}
    try:
        address = ipaddress.ip_address(hostname)
        local_ip = address.is_private or address.is_loopback
    except ValueError:
        local_ip = False

    if (
        hostname not in local_names
        and not hostname.endswith(".localhost")
        and not local_ip
    ):
        raise ValueError("TARGET_URL must point to localhost or a private app host")

    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def request_origin(url: str):
    parsed = urlsplit(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))


def navigate(page: Page, url: str):
    return page.goto(url, wait_until="domcontentloaded")


def wait_for_app(page: Page, base_url: str):
    emit("waiting_for_app", target=base_url)
    while True:
        try:
            response = page.goto(
                base_url,
                wait_until="domcontentloaded",
                timeout=5000,
            )
            if response is not None and response.status < 500:
                emit("app_available", status=response.status)
                return
        except PlaywrightError:
            pass
        time.sleep(2)


def login(page: Page, base_url: str):
    navigate(page, f"{base_url}/login")
    page.locator("input[name='username']").fill(ATTACKER_USERNAME)
    page.locator("input[name='password']").fill(ATTACKER_PASSWORD)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{base_url}/")
    page.get_by_text(f"Note it, {ATTACKER_USERNAME}").wait_for()


def register_or_login(page: Page, base_url: str):
    navigate(page, f"{base_url}/register")
    page.locator("input[name='username']").fill(ATTACKER_USERNAME)
    page.locator("input[name='password']").fill(ATTACKER_PASSWORD)
    page.locator("input[name='confirm_password']").fill(ATTACKER_PASSWORD)
    page.get_by_role("button", name="Create account").click()

    if "Account created" in page.locator("body").inner_text():
        emit("actor_account_created", username=ATTACKER_USERNAME)
    else:
        emit("actor_account_reused", username=ATTACKER_USERNAME)

    login(page, base_url)


def restrict_to_app_origin(route: Route, base_url: str):
    request_url = route.request.url
    if request_origin(request_url) == base_url:
        route.continue_()
    else:
        emit("external_request_blocked", url=request_url)
        route.abort()
