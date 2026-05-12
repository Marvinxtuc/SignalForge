#!/usr/bin/env python3
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]

SCAN_TARGETS = [
    "apps",
    "infra",
    "scripts",
    "docs",
    "sop",
    ".github",
    "README.md",
    ".env.example",
]

OPTIONAL_MISSING = {"apps", "infra"}
REQUIRED_MISSING = {"docs", "sop", ".github", "README.md", ".env.example"}

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "dist",
    "build",
    ".next",
    "__pycache__",
    ".pytest_cache",
}

SECRET_PATTERNS = [
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{18,}\b")),
    ("reddit_client_secret_assignment", re.compile(r"REDDIT_CLIENT_SECRET\s*=\s*['\"]?[A-Za-z0-9_-]{16,}")),
    ("product_hunt_token_assignment", re.compile(r"PRODUCT_HUNT_TOKEN\s*=\s*['\"]?[A-Za-z0-9._-]{16,}")),
    ("discord_token_assignment", re.compile(r"DISCORD_BOT_TOKEN\s*=\s*['\"]?[A-Za-z0-9._-]{24,}")),
    ("x_bearer_token_assignment", re.compile(r"X_BEARER_TOKEN\s*=\s*['\"]?[A-Za-z0-9._-]{20,}")),
    ("generic_bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9._-]{20,}\b")),
    ("private_key_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("secret_like_assignment", re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?[A-Za-z0-9._/-]{32,}")),
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def iter_files(path: Path):
    if path.is_file():
        yield path
        return
    for child in path.rglob("*"):
        if child.is_dir():
            continue
        if any(part in SKIP_DIRS for part in child.relative_to(ROOT).parts):
            continue
        yield child


def is_binary(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:1024]
    except OSError:
        return True
    return b"\0" in chunk


def main() -> None:
    if (ROOT / ".env").exists():
        fail(".env file must not be committed or present in repository root")

    files = []
    for target in SCAN_TARGETS:
        path = ROOT / target
        if not path.exists():
            if target in OPTIONAL_MISSING:
                print(f"SKIP: optional path missing in Phase -1: {target}")
                continue
            if target in REQUIRED_MISSING:
                fail(f"required path missing: {target}")
        files.extend(iter_files(path))

    for file_path in files:
        if is_binary(file_path):
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in SECRET_PATTERNS:
            for line_no, line in enumerate(text.splitlines(), start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if "re.compile" in stripped:
                    continue
                if "process.env." in stripped or "os.getenv(" in stripped or "os.environ" in stripped:
                    continue
                if pattern.search(stripped):
                    rel = file_path.relative_to(ROOT)
                    fail(f"possible secret {name} in {rel}:{line_no}")

    print("PASS: no secrets validation")


if __name__ == "__main__":
    main()
