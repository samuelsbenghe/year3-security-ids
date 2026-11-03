import json
import os
import time
from pathlib import Path


def emit(kind: str, **details: object) -> None:
    event: dict[str, object] = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": kind,
        **details,
    }
    line = json.dumps(event)
    log_path = os.getenv("ATTACKER_LOG_PATH")
    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as log_file:
            log_file.write(line + "\n")
    print(line, flush=True)
