#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "backups"
COMPOSE = ROOT / "infra" / "docker-compose.production.yml"
ENV_FILE = ROOT / ".env.production.local"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Mac local production PostgreSQL backup.")
    parser.add_argument("--output-dir", default=str(BACKUP_DIR))
    parser.add_argument("--database", default="signalforge")
    parser.add_argument("--user", default="signalforge")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"signalforge-production-{stamp}.dump"

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
        "pg_dump",
        "-Fc",
        "-U",
        args.user,
        "-d",
        args.database,
    ]
    with output_path.open("wb") as handle:
        result = subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.PIPE, check=False)

    if result.returncode != 0:
        output_path.unlink(missing_ok=True)
        sys.stderr.write(result.stderr.decode("utf-8", errors="replace"))
        return result.returncode

    print(f"PASS: backup written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
