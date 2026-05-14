#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import socket
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_COMPOSE = ROOT / "infra" / "docker-compose.production.yml"
DEFAULT_ENV_FILE = ROOT / ".env.production.local"
REQUIRED_ENV_NAMES = (
    "DATABASE_URL",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
)
OWNER_AUTH_ENV_NAMES = (
    "SIGNALFORGE_OWNER_USERNAME",
    "SIGNALFORGE_OWNER_PASSWORD",
    "SIGNALFORGE_OWNER_SESSION_TOKEN",
    "SIGNALFORGE_OWNER_API_TOKEN",
    "SIGNALFORGE_SESSION_SECRET",
)
TRUE_VALUES = {"1", "true", "yes", "on"}
FORBIDDEN_TUNNEL_MARKERS = ("cloudflared", "trycloudflare", "ngrok")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def warn(message: str) -> None:
    print(f"WARN: {message}")


def pass_(message: str) -> None:
    print(f"PASS: {message}")


def read_env_names(path: Path) -> set[str]:
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        names.add(stripped.split("=", 1)[0].strip())
    return names


def read_env_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        values[name.strip()] = value.strip()
    return values


def validate_env_file(path: Path, *, strict: bool) -> None:
    if not path.exists():
        if strict:
            fail(f"production env file is missing: {path}")
        warn(f"production env file is missing: {path}")
        return

    values = read_env_values(path)
    names = set(values)
    missing = [name for name in REQUIRED_ENV_NAMES if name not in names]
    if missing:
        fail("production env file missing required name(s): " + ", ".join(missing))

    owner_auth_enabled = values.get("SIGNALFORGE_REQUIRE_OWNER_AUTH", "").strip().lower() in TRUE_VALUES
    if owner_auth_enabled:
        missing_owner = [name for name in OWNER_AUTH_ENV_NAMES if name not in names]
        if missing_owner:
            fail("owner auth env file missing required name(s): " + ", ".join(missing_owner))

    checked_names = set(REQUIRED_ENV_NAMES)
    if owner_auth_enabled:
        checked_names.update(OWNER_AUTH_ENV_NAMES)

    placeholder_names = [
        name
        for name, value in values.items()
        if name in checked_names
        and ("change-me" in value.lower() or value.strip().lower() in {"", "password", "secret"})
    ]
    if placeholder_names:
        fail("production env file contains placeholder value(s): " + ", ".join(placeholder_names))
    pass_("production env file contains required names")


def validate_compose_static() -> None:
    if not PRODUCTION_COMPOSE.is_file():
        fail(f"missing production compose file: {PRODUCTION_COMPOSE}")

    text = PRODUCTION_COMPOSE.read_text(encoding="utf-8")
    if re.search(r"(?m)^\s+env_file:\s*$", text):
        fail("production compose must not inject the full env file into service containers")

    if '"127.0.0.1:3000:3000"' not in text and "'127.0.0.1:3000:3000'" not in text:
        fail("web service must bind to 127.0.0.1:3000")

    if 'SIGNALFORGE_REQUIRE_OWNER_AUTH: "false"' not in text:
        fail("Mac local production compose must disable owner password login by default")

    if "SIGNALFORGE_OWNER_PASSWORD: ${SIGNALFORGE_OWNER_PASSWORD:?" in text:
        fail("Mac local production compose must not require an owner password")

    forbidden_patterns = [
        r"(?m)^\s*-\s*[\"']?0\.0\.0\.0:",
        r"(?m)^\s*-\s*[\"']?(8000|5432|6379):",
        r"(?m)^\s*ports:\s*$[\s\S]{0,160}?(api|postgres|redis)",
    ]
    for pattern in forbidden_patterns[:2]:
        if re.search(pattern, text):
            fail("production compose contains forbidden public or service port binding")

    for service in ("api", "postgres", "redis"):
        block = service_block(text, service)
        if re.search(r"(?m)^\s+ports:\s*$", block):
            fail(f"{service} service must not publish host ports")

    pass_("production compose exposes only localhost web port")


def service_block(text: str, service: str) -> str:
    match = re.search(rf"(?ms)^  {re.escape(service)}:\n(.*?)(?=^  [a-zA-Z0-9_-]+:|\Z)", text)
    return match.group(0) if match else ""


def validate_no_tunnel_process() -> None:
    result = subprocess.run(
        ["pgrep", "-fl", "|".join(FORBIDDEN_TUNNEL_MARKERS)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    output = result.stdout.strip()
    if output:
        fail("forbidden tunnel process detected:\n" + output)
    pass_("no cloudflared/trycloudflare/ngrok process detected")


def validate_no_forbidden_listeners() -> None:
    forbidden_ports = (8000, 5432, 6379)
    for port in forbidden_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                fail(f"forbidden local production listener is reachable on 127.0.0.1:{port}")
    pass_("api/postgres/redis are not reachable on host default ports")


def run_no_secrets() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_no_secrets.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        sys.exit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate SignalForge Mac local production safety.")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument("--strict-env", action="store_true")
    parser.add_argument("--skip-listener-check", action="store_true")
    args = parser.parse_args()

    validate_compose_static()
    validate_env_file(Path(args.env_file), strict=args.strict_env)
    validate_no_tunnel_process()
    if not args.skip_listener_check:
        validate_no_forbidden_listeners()
    run_no_secrets()
    pass_("Mac mini local production static safety validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
