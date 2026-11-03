from playwright.sync_api import Page

from browser import navigate, origin
from settings import SQL_NOTE_PAYLOADS, suspicious_paths
from logs import emit


def probe_suspicious_path(page: Page, base_url: str, cycle: int):
    path = suspicious_paths[cycle % len(suspicious_paths)]
    response = navigate(page, f"{base_url}{path}")
    final_url = page.url

    if origin(final_url) != base_url:
        raise RuntimeError(f"Probe redirected outside the app origin: {final_url}")

    emit(
        "suspicious_path_probe",
        path=path,
        status=response.status if response else None,
        final_url=final_url,
    )


def publish_sql_note(page: Page, base_url: str, note_index: int):
    content = SQL_NOTE_PAYLOADS[note_index % len(SQL_NOTE_PAYLOADS)]

    navigate(page, f"{base_url}/notes")
    page.locator("textarea[name='content']").fill(content)
    page.get_by_role("button", name="Publish note").click()
    page.wait_for_url(f"{base_url}/")
    newest_note = page.locator("article.note").first.locator("p")
    newest_note.wait_for()
    if newest_note.inner_text().strip() != content:
        raise RuntimeError("The newly published note was not shown first")

    emit("sql_note_probe", result="stored_as_note_text", content=content)
