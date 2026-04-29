#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.client
import json
import socket
import sys
import time
from urllib.parse import urlparse


def wait_for_http(name: str, url: str, timeout: float) -> None:
    parsed = urlparse(url)
    deadline = time.monotonic() + timeout
    last_error = ""

    while time.monotonic() < deadline:
        try:
            conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
            conn = conn_cls(parsed.hostname, parsed.port, timeout=3)
            path = parsed.path or "/"
            conn.request("GET", path)
            response = conn.getresponse()
            body = response.read().decode("utf-8", errors="replace")
            conn.close()
            if 200 <= response.status < 400:
                if name == "api":
                    payload = json.loads(body)
                    if payload.get("status") != "ok":
                        raise RuntimeError(f"unexpected API health payload: {payload}")
                print(f"PASS: {name} ready at {url}")
                return
            last_error = f"HTTP {response.status}: {body[:160]}"
        except Exception as exc:  # noqa: BLE001 - readable readiness error
            last_error = str(exc)
        time.sleep(1)

    raise TimeoutError(f"{name} not ready after {timeout:.0f}s: {last_error}")


def wait_for_tcp(name: str, host: str, port: int, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error = ""

    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                print(f"PASS: {name} TCP ready at {host}:{port}")
                return
        except OSError as exc:
            last_error = str(exc)
        time.sleep(1)

    raise TimeoutError(f"{name} TCP not ready after {timeout:.0f}s: {last_error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait for SignalForge Phase 0 services.")
    parser.add_argument("--api-url", default="http://localhost:8000/health")
    parser.add_argument("--web-url", default="http://localhost:3000/")
    parser.add_argument("--postgres-host", default="localhost")
    parser.add_argument("--postgres-port", type=int, default=5432)
    parser.add_argument("--redis-host", default="localhost")
    parser.add_argument("--redis-port", type=int, default=6379)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()

    try:
        wait_for_tcp("postgres", args.postgres_host, args.postgres_port, args.timeout)
        wait_for_tcp("redis", args.redis_host, args.redis_port, args.timeout)
        wait_for_http("api", args.api_url, args.timeout)
        wait_for_http("web", args.web_url, args.timeout)
    except Exception as exc:  # noqa: BLE001 - command-line validation
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: all Phase 0 services are ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
