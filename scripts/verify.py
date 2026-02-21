#!/usr/bin/env python3
"""
Repository verification checks for local development.

What this script does:
- Loads .env (without overriding existing shell env)
- Runs repository formatting/lint checks via pre-commit
- Validates required env vars
- Optionally checks API health endpoint
- Optionally checks database connectivity (psycopg / psycopg2 / psql)
- Prints PASS/FAIL per check and exits non-zero on failure
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


ROOT_DIR = Path(__file__).resolve().parents[1]
DOTENV_PATH = ROOT_DIR / ".env"

REQUIRED_ENV_VARS = {
    "OWNER_API_KEY": "Single-owner API key for protected backend routes.",
    "API_HEALTH_URL": "HTTP endpoint for API health checks (example: http://localhost:8000/health).",
    "DATABASE_URL": "PostgreSQL connection string used to confirm DB connectivity.",
}


# ---------------------------
# Helpers / output formatting
# ---------------------------

def print_check(name: str, ok: bool, details: str) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}")
    if details:
        for line in details.splitlines():
            print(f"       {line}")


def redact_secrets(text: str) -> str:
    """
    Best-effort redaction for common secrets in logs:
    - Masks credentials embedded in URLs: scheme://user:pass@host -> scheme://***@host
    - Masks DATABASE_URL value if it appears verbatim
    """
    if not text:
        return text

    # Mask any URL credentials (very simple heuristic)
    # Finds "://...@" and replaces inner portion.
    out = text
    while True:
        idx = out.find("://")
        if idx == -1:
            break
        at = out.find("@", idx + 3)
        if at == -1:
            break
        # Only redact if there's at least one ":" between :// and @ (user:pass)
        creds_segment = out[idx + 3 : at]
        if ":" in creds_segment:
            out = out[: idx + 3] + "***@" + out[at + 1 :]
        else:
            # no user:pass, stop trying for this occurrence
            break

    # Mask explicit DATABASE_URL if present
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url and db_url in out:
        out = out.replace(db_url, "<DATABASE_URL_REDACTED>")

    return out


# ---------------------------
# .env loading + env validation
# ---------------------------

def load_dotenv(path: Path) -> int:
    """Load key/value pairs from .env into process env without overriding already-set vars."""
    if not path.exists():
        return 0

    loaded = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        # strip optional quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]

        if key not in os.environ:
            os.environ[key] = value
            loaded += 1

    return loaded


def validate_required_env(required: dict[str, str]) -> tuple[bool, str]:
    missing: list[tuple[str, str]] = []
    for key, purpose in required.items():
        if not os.environ.get(key, "").strip():
            missing.append((key, purpose))

    if not missing:
        return True, "All required environment variables are set."

    lines = ["Missing required environment variables:"]
    for key, purpose in missing:
        lines.append(f"- {key}: {purpose}")
    lines.append("Define them in .env or export them in your shell and run verify again.")
    return False, "\n".join(lines)


# ---------------------------
# API health check
# ---------------------------

def check_api_health(url: str, timeout_s: float, hint: Optional[str] = None) -> tuple[bool, str]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})

    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            status = response.getcode()
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        details = f"Health endpoint {url} is unreachable: {reason}"
        if hint:
            details += f"\nTry: {hint}"
        return False, redact_secrets(details)
    except Exception as exc:
        details = f"Unexpected error calling health endpoint {url}: {exc}"
        if hint:
            details += f"\nTry: {hint}"
        return False, redact_secrets(details)

    if 200 <= status < 300:
        return True, f"Health endpoint responded successfully with HTTP {status}."
    details = f"Health endpoint returned non-success HTTP status {status}."
    if hint:
        details += f"\nTry: {hint}"
    return False, redact_secrets(details)


# ---------------------------
# DB connectivity checks
# ---------------------------

@dataclass(frozen=True)
class DbMethodResult:
    ok: bool
    details: str
    attempted: bool = True  # false if method unavailable


DbCheckFn = Callable[[str, float], DbMethodResult]


def _check_db_with_psycopg(database_url: str, timeout_s: float) -> DbMethodResult:
    try:
        import psycopg  # type: ignore
    except ImportError:
        return DbMethodResult(False, "psycopg is not installed.", attempted=False)

    try:
        with psycopg.connect(database_url, connect_timeout=int(timeout_s)) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return DbMethodResult(True, "Connected to PostgreSQL with psycopg and executed SELECT 1.")
    except Exception as exc:
        return DbMethodResult(False, redact_secrets(f"Failed to connect/query PostgreSQL with psycopg: {exc}"))


def _check_db_with_psycopg2(database_url: str, timeout_s: float) -> DbMethodResult:
    try:
        import psycopg2  # type: ignore
    except ImportError:
        return DbMethodResult(False, "psycopg2 is not installed.", attempted=False)

    try:
        conn = psycopg2.connect(database_url, connect_timeout=int(timeout_s))
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        finally:
            conn.close()
        return DbMethodResult(True, "Connected to PostgreSQL with psycopg2 and executed SELECT 1.")
    except Exception as exc:
        return DbMethodResult(False, redact_secrets(f"Failed to connect/query PostgreSQL with psycopg2: {exc}"))


def _check_db_with_psql(database_url: str, timeout_s: float) -> DbMethodResult:
    if not shutil.which("psql"):
        return DbMethodResult(False, "psql is not available on PATH.", attempted=False)

    try:
        result = subprocess.run(
            ["psql", database_url, "-tAc", "SELECT 1"],
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout_s * 2)),
            check=False,
        )
    except Exception as exc:
        return DbMethodResult(False, redact_secrets(f"Failed to execute psql check: {exc}"))

    output = (result.stdout or "").strip()
    if result.returncode == 0 and output == "1":
        return DbMethodResult(True, "Connected to PostgreSQL with psql and executed SELECT 1.")

    err = (result.stderr or "").strip()
    details = err if err else f"psql returned code {result.returncode}."
    return DbMethodResult(False, redact_secrets(f"Failed to connect/query PostgreSQL with psql: {details}"))


def check_database_connection(
    database_url: str,
    timeout_s: float,
    hint: Optional[str] = None,
) -> tuple[bool, str]:
    methods: list[tuple[str, DbCheckFn]] = [
        ("psycopg", _check_db_with_psycopg),
        ("psycopg2", _check_db_with_psycopg2),
        ("psql", _check_db_with_psql),
    ]

    unavailable: list[str] = []
    for name, fn in methods:
        res = fn(database_url, timeout_s)
        if not res.attempted:
            unavailable.append(res.details)
            continue
        if res.ok:
            return True, res.details
        # attempted but failed
        details = res.details
        if hint:
            details += f"\nTry: {hint}"
        return False, details

    # none attempted
    lines = [
        "No PostgreSQL client available for DB verification.",
        "Install one of the following or ensure it is available on PATH:",
        "- psycopg (recommended)  OR",
        "- psycopg2              OR",
        "- psql (PostgreSQL CLI)",
    ]
    if unavailable:
        lines.append("")
        lines.append("Detected missing tools:")
        for msg in unavailable:
            lines.append(f"- {msg}")
    if hint:
        lines.append("")
        lines.append(f"Try: {hint}")
    return False, "\n".join(lines)


# ---------------------------
# Formatting and lint checks
# ---------------------------

def _tail_lines(text: str, limit: int = 20) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) <= limit:
        return "\n".join(lines)
    return "\n".join(lines[-limit:])


def check_format_and_lint(timeout_s: float) -> tuple[bool, str]:
    if not shutil.which("pre-commit"):
        return (
            False,
            "pre-commit is not installed. Install it with `pip install pre-commit` and run `pre-commit install`.",
        )

    try:
        result = subprocess.run(
            ["pre-commit", "run", "--all-files"],
            capture_output=True,
            text=True,
            timeout=max(30, int(timeout_s * 30)),
            check=False,
        )
    except Exception as exc:
        return False, f"Failed to execute pre-commit checks: {exc}"

    if result.returncode == 0:
        return True, "pre-commit formatting and lint hooks passed."

    combined_output = "\n".join(part for part in [result.stdout, result.stderr] if part).strip()
    if not combined_output:
        combined_output = "pre-commit failed without output."
    details = _tail_lines(combined_output, limit=25)
    return False, f"pre-commit reported issues:\n{details}"


# ---------------------------
# Main
# ---------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify local dev setup for this repository.")
    p.add_argument("--skip-style", action="store_true", help="Skip formatting and lint checks.")
    p.add_argument("--skip-api", action="store_true", help="Skip the API health endpoint check.")
    p.add_argument("--skip-db", action="store_true", help="Skip the database connectivity check.")
    p.add_argument("--timeout", type=float, default=5.0, help="Timeout (seconds) for network/DB checks.")
    p.add_argument(
        "--services-hint",
        default="docker compose up -d",
        help="Command hint to start services (shown on API/DB failures).",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    print("Running repository verification checks...\n")

    loaded_count = load_dotenv(DOTENV_PATH)
    if DOTENV_PATH.exists():
        print(f"Loaded {loaded_count} value(s) from .env\n")
    else:
        print("No .env file found. Using existing shell environment values only.\n")

    all_ok = True

    if args.skip_style:
        print_check("Formatting and linting", True, "Skipped (--skip-style).")
    else:
        style_ok, style_details = check_format_and_lint(timeout_s=args.timeout)
        print_check("Formatting and linting", style_ok, style_details)
        all_ok = all_ok and style_ok

    env_ok, env_details = validate_required_env(REQUIRED_ENV_VARS)
    print_check("Environment variables", env_ok, env_details)
    if not env_ok:
        print("\nVerification completed.")
        print("Result: FAIL")
        return 1

    if args.skip_api:
        print_check("API health endpoint", True, "Skipped (--skip-api).")
    else:
        api_url = os.environ["API_HEALTH_URL"]
        api_ok, api_details = check_api_health(api_url, timeout_s=args.timeout, hint=args.services_hint)
        print_check("API health endpoint", api_ok, api_details)
        all_ok = all_ok and api_ok

    if args.skip_db:
        print_check("Database connection", True, "Skipped (--skip-db).")
    else:
        db_url = os.environ["DATABASE_URL"]
        db_ok, db_details = check_database_connection(
            db_url, timeout_s=args.timeout, hint=args.services_hint
        )
        print_check("Database connection", db_ok, db_details)
        all_ok = all_ok and db_ok

    print("\nVerification completed.")
    print("Result: PASS" if all_ok else "Result: FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
