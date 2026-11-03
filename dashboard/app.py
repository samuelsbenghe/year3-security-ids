import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
MAX_LOG_BYTES = 1024 * 1024
MAX_LOG_LINES = 200
TABS = {"suricata": "Suricata", "attacker": "Attacker", "web": "Web"}


def read_log(path_value: str | None) -> str:
    if not path_value:
        return "Log path is not configured."

    path = Path(path_value)
    try:
        with path.open("rb") as log_file:
            log_file.seek(0, os.SEEK_END)
            size = log_file.tell()
            log_file.seek(max(0, size - MAX_LOG_BYTES))
            data = log_file.read()
    except FileNotFoundError:
        return "No log entries yet."
    except OSError as error:
        return f"Could not read log: {error}"

    lines = data.decode("utf-8", errors="replace").splitlines()
    if size > MAX_LOG_BYTES and lines:
        lines = lines[1:]
    return "\n".join(lines[-MAX_LOG_LINES:]) or "No log entries yet."


@app.get("/")
def index():
    active_tab = request.args.get("tab", "suricata")
    if active_tab not in TABS:
        active_tab = "suricata"

    return render_template("index.html", tabs=TABS, active_tab=active_tab)


@app.get("/logs/<tab>")
def logs(tab: str):
    if tab not in TABS:
        return jsonify({"error": "Unknown log tab"}), 404

    content = {
        "suricata": lambda: read_log(os.getenv("SURICATA_LOG_PATH")),
        "attacker": lambda: read_log(os.getenv("ATTACKER_LOG_PATH")),
        "web": lambda: "\n\n".join(
            (
                "=== Access log ===\n" + read_log(os.getenv("WEB_ACCESS_LOG_PATH")),
                "=== Error log ===\n" + read_log(os.getenv("WEB_ERROR_LOG_PATH")),
            )
        ),
    }[tab]()
    return jsonify({"content": content})
