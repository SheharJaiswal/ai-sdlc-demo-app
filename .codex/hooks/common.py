"""Shared, standard-library-only helpers for sanitized Codex hook events."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_TEXT_LENGTH = 2_000

# Match common credential-bearing assignments, including quoted values with spaces.
# For unquoted values, consume to a JSON/YAML-ish delimiter or end of line.
_SECRET_ASSIGNMENT = re.compile(
    r"""(?im)(\b(?:password|passwd|passphrase|api[_-]?key|access[_-]?token|refresh[_-]?token|"""
    r"""id[_-]?token|client[_-]?secret|secret[_-]?key|aws[_-]?secret[_-]?access[_-]?key|"""
    r"""private[_-]?key|authorization|proxy[_-]?authorization|credential|connection[_-]?string|token)\b"""
    r"""\s*[:=]\s*)(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\r\n,;}\]]*)"""
)
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z0-9 ]*PRIVATE KEY-----"
)
_BEARER = re.compile(r"(?i)\b(Bearer\s+)[A-Za-z0-9._~+/-]+=*")
_BASIC = re.compile(r"(?i)\b(Basic\s+)[A-Za-z0-9+/]+={0,2}")
_GITHUB_TOKEN = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")
_AWS_ACCESS_KEY = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b")
_OPENAI_STYLE_KEY = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def hash_identifier(value: object) -> str | None:
    if value in (None, ""):
        return None
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()
    return f"sha256:{digest[:16]}"


def redact_text(value: object) -> str:
    """Redact recognizable secrets before text is written to a local audit log.

    This is defense in depth, not a guarantee that arbitrary high-entropy secrets
    can be recognized. Keep raw tool responses and transcripts out of the log.
    """
    text = str(value or "")
    text = _PRIVATE_KEY.sub("[REDACTED_PRIVATE_KEY]", text)
    text = _SECRET_ASSIGNMENT.sub(r"\1[REDACTED]", text)
    text = _BEARER.sub(r"\1[REDACTED]", text)
    text = _BASIC.sub(r"\1[REDACTED]", text)
    text = _GITHUB_TOKEN.sub("[REDACTED_TOKEN]", text)
    text = _AWS_ACCESS_KEY.sub("[REDACTED_AWS_ACCESS_KEY]", text)
    text = _JWT.sub("[REDACTED_JWT]", text)
    text = _OPENAI_STYLE_KEY.sub("[REDACTED_TOKEN]", text)
    return text[:MAX_TEXT_LENGTH]


def read_hook_input() -> dict[str, Any]:
    import sys

    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Hook input must be a JSON object.")
    return value


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def log_path() -> Path:
    configured = os.environ.get("AI_SDL_LOG_PATH")
    return Path(configured) if configured else repo_root() / ".codex" / "local" / "ai-interactions.jsonl"


def append_event(event: dict[str, Any]) -> None:
    """Append one event with owner-only permissions where the OS supports them."""
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    descriptor = os.open(path, flags, 0o600)
    try:
        try:
            os.chmod(path, 0o600)
        except OSError:
            # Windows ACLs, not POSIX mode bits, are the effective control there.
            pass
        with os.fdopen(descriptor, "a", encoding="utf-8", newline="\n") as stream:
            descriptor = -1
            stream.write(json.dumps(event, sort_keys=True, ensure_ascii=True) + "\n")
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def append_event_best_effort(event: dict[str, Any]) -> bool:
    """Keep lifecycle logging observable without making an unavailable log fatal."""
    import sys

    try:
        append_event(event)
    except OSError as error:
        print(f"AI SDLC hook logging unavailable: {type(error).__name__}", file=sys.stderr)
        return False
    return True


def base_event(payload: dict[str, Any], event_type: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "timestamp": utc_now(),
        "event_type": event_type,
        "session_id": hash_identifier(payload.get("session_id")),
        "turn_id": hash_identifier(payload.get("turn_id")),
        "model": redact_text(payload.get("model")),
        "cwd": redact_text(payload.get("cwd")),
    }


def safe_tool_outcome(tool_response: object) -> dict[str, Any]:
    """Preserve only shape metadata; never persist unrestricted tool output."""
    return {
        "response_available": tool_response is not None,
        "response_type": type(tool_response).__name__ if tool_response is not None else None,
    }
