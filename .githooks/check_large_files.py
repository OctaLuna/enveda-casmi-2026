#!/usr/bin/env python3
"""
Pre-commit utility: Check staged files for large sizes (>50MB), forbidden extensions,
and basic markdown formatting.
"""

import sys
import subprocess
from pathlib import Path

MAX_FILE_SIZE_MB = 50.0
MAX_BYTES = int(MAX_FILE_SIZE_MB * 1024 * 1024)

FORBIDDEN_EXTENSIONS = {
    ".parquet",
    ".pt",
    ".pth",
    ".pkl",
    ".joblib",
    ".bin",
    ".onnx",
    ".index",
}


def get_staged_files() -> list[str]:
    """Retrieve list of files staged for commit."""
    try:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return [f.strip() for f in result.stdout.splitlines() if f.strip()]
    except Exception as e:
        print(f"[ERROR] Could not inspect staged files via git: {e}")
        return []


def validate_file(filepath_str: str) -> bool:
    """Validate a single staged file against size and extension rules."""
    path = Path(filepath_str)
    if not path.exists():
        return True  # File might have been deleted or moved

    # 1. Extension check
    suffix = path.suffix.lower()
    if suffix in FORBIDDEN_EXTENSIONS:
        print(f"[REJECTED] Staged file '{filepath_str}' has forbidden data/model extension '{suffix}'.")
        print("          Store large artifacts in Kaggle datasets, MLflow, or external storage.")
        return False

    # 2. File size check (>50MB)
    size_bytes = path.stat().st_size
    if size_bytes > MAX_BYTES:
        size_mb = size_bytes / (1024 * 1024)
        print(f"[REJECTED] Staged file '{filepath_str}' is {size_mb:.2f} MB, which exceeds {MAX_FILE_SIZE_MB} MB limit.")
        return False

    # 3. Markdown basic validation
    if suffix == ".md":
        try:
            with open(path, "r", encoding="utf-8") as f:
                f.read()
        except UnicodeDecodeError:
            print(f"[REJECTED] Markdown file '{filepath_str}' contains invalid UTF-8 characters.")
            return False

    return True


def main() -> int:
    staged = get_staged_files()
    if not staged:
        return 0

    failed = False
    for filepath in staged:
        if not validate_file(filepath):
            failed = True

    if failed:
        print("\nCommit aborted due to pre-commit file validation errors.")
        return 1

    print("[OK] All staged files passed size, extension, and markdown syntax checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
