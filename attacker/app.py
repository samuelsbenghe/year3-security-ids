import time

from playwright.sync_api import sync_playwright

from browser import (
    origin,
    register_or_login,
    restrict_to_app_origin,
    wait_for_app,
)
from settings import (
    INTERVAL_SECONDS,
    NOTE_INTERVAL_SECONDS,
    TARGET_URL,
    validate_settings,
)
from logs import emit
from probes import probe_suspicious_path, publish_sql_note


def run_attacker(page, base_url: str):
    cycle = 0
    note_index = 0
    last_note_at = time.monotonic() - NOTE_INTERVAL_SECONDS

    while True:
        started_at = time.monotonic()
        try:
            probe_suspicious_path(page, base_url, cycle)
            emit("probe_cycle_completed", cycle=cycle + 1)
        except Exception as error:
            emit(
                "probe_cycle_error",
                cycle=cycle + 1,
                error=type(error).__name__,
                detail=str(error)[:300],
            )

        now = time.monotonic()
        if now - last_note_at >= NOTE_INTERVAL_SECONDS:
            last_note_at = now
            try:
                publish_sql_note(page, base_url, note_index)
                note_index += 1
            except Exception as error:
                emit(
                    "note_probe_error",
                    error=type(error).__name__,
                    detail=str(error)[:300],
                )

        cycle += 1
        elapsed = time.monotonic() - started_at
        time.sleep(max(0, INTERVAL_SECONDS - elapsed))


def main():
    validate_settings()
    base_url = origin(TARGET_URL).rstrip("/")
    emit(
        "attacker_started",
        target=base_url,
        interval_seconds=INTERVAL_SECONDS,
        note_interval_seconds=NOTE_INTERVAL_SECONDS,
        workers=1,
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            try:
                context.route(
                    "**/*",
                    lambda route: restrict_to_app_origin(route, base_url),
                )
                page = context.new_page()
                wait_for_app(page, base_url)
                register_or_login(page, base_url)
                run_attacker(page, base_url)
            finally:
                context.close()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
