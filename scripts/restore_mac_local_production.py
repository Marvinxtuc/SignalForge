#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "infra" / "docker-compose.production.yml"
ENV_FILE = ROOT / ".env.production.local"


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore a Mac local production PostgreSQL backup.")
    parser.add_argument("--backup-file", required=True)
    parser.add_argument("--database", default="signalforge")
    parser.add_argument("--user", default="signalforge")
    parser.add_argument("--confirm-restore", action="store_true")
    args = parser.parse_args()

    backup_path = Path(args.backup_file).expanduser().resolve()
    if not backup_path.is_file():
        sys.stderr.write(f"FAIL: backup file does not exist: {backup_path}\n")
        return 1
    if not args.confirm_restore:
        print("FAIL: restore is destructive; rerun with --confirm-restore after verifying the backup path.")
        return 1

    command = [
        "docker",
        "compose",
        "--env-file",
        str(ENV_FILE),
        "-f",
        str(COMPOSE),
        "exec",
        "-T",
        "postgres",
        "pg_restore",
        "--clean",
        "--if-exists",
        "-U",
        args.user,
        "-d",
        args.database,
    ]
    with backup_path.open("rb") as handle:
        result = subprocess.run(command, cwd=ROOT, stdin=handle, stderr=subprocess.PIPE, check=False)

    if result.returncode != 0:
        sys.stderr.write(result.stderr.decode("utf-8", errors="replace"))
        return result.returncode

    print(f"PASS: restored backup from {backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
