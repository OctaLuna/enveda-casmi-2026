"""Shared standard-library utilities for repository governance hooks."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from typing import Any


def find_project_root(start: str | Path | None = None) -> Path | None:
    """Find the repository root by locating its agent configuration or Git dir."""
    current = Path(start or Path.cwd()).expanduser().resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / ".agents" / "project.json").is_file():
            return candidate
        if (candidate / ".git").exists():
            return candidate
    return None


def load_project_config(root: str | Path | None = None) -> dict[str, Any]:
    """Load `.agents/project.json`; return an empty mapping if unavailable."""
    project_root = Path(root).resolve() if root else find_project_root()
    if project_root is None:
        return {}
    config_path = project_root / ".agents" / "project.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log_error("common.load_project_config", f"Cannot load {config_path}: {exc}")
        return {}
    return config if isinstance(config, dict) else {}


def read_stdin_payload() -> dict[str, Any]:
    """Read a JSON object from stdin, returning an empty mapping when absent."""
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        log_error("common.read_stdin_payload", f"Invalid JSON input: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def match_any_glob(path: str | Path, patterns: list[str] | tuple[str, ...]) -> bool:
    """Match a path against POSIX-style globs, including repo-relative paths."""
    raw_path = str(path).replace("\\", "/")
    candidates = {raw_path}
    path_obj = Path(path)
    root = find_project_root()
    if root and path_obj.is_absolute():
        try:
            candidates.add(path_obj.resolve().relative_to(root).as_posix())
        except ValueError:
            pass

    for pattern in patterns:
        normalized_pattern = str(pattern).replace("\\", "/")
        if any(
            fnmatch.fnmatchcase(candidate, normalized_pattern)
            or Path(candidate).match(normalized_pattern)
            for candidate in candidates
        ):
            return True
    return False


def ensure_state_dir(root: str | Path | None = None) -> Path:
    """Create and return the ignored `.agents/state` directory."""
    project_root = Path(root).resolve() if root else find_project_root()
    if project_root is None:
        project_root = Path.cwd().resolve()
    state_dir = project_root / ".agents" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def _append_state_log(filename: str, line: str) -> None:
    try:
        path = ensure_state_dir() / filename
        with path.open("a", encoding="utf-8") as log_file:
            log_file.write(line.rstrip() + "\n")
    except OSError:
        # Logging must not prevent a safety hook from enforcing its decision.
        pass


def log_activity(message: str) -> None:
    """Append an activity line to the ignored project state log."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _append_state_log("activity.log", f"{timestamp} {message}")


def log_error(hook_id: str, message: str) -> None:
    """Record a hook infrastructure or execution error locally."""
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _append_state_log("errors.log", f"{timestamp} [{hook_id}] {message}")


def warn(message: str, hook_id: str | None = None) -> None:
    """Write a non-blocking diagnostic to stderr."""
    prefix = f"[{hook_id}] " if hook_id else ""
    print(f"WARN: {prefix}{message}", file=sys.stderr)


def block(
    message: str,
    hook_id: str | None = None,
    reason: str | None = None,
    solution: str | None = None,
) -> None:
    """Emit a blocking diagnostic and terminate the hook with exit code 2."""
    prefix = f"[{hook_id}] " if hook_id else ""
    print(f"BLOCK: {prefix}{message}", file=sys.stderr)
    if reason:
        print(f"Reason: {reason}", file=sys.stderr)
    if solution:
        print(f"Solution: {solution}", file=sys.stderr)
    raise SystemExit(2)
