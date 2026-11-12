"""Record sanitized lifecycle metadata. Raw tool responses and transcripts are excluded."""

from __future__ import annotations

import sys
import os

from common import append_event_best_effort, base_event, hash_identifier, read_hook_input, redact_text, safe_tool_outcome


def event_for(event_type: str, payload: dict) -> dict:
    event = base_event(payload, event_type)
    if event_type == "UserPromptSubmit":
        event["prompt_length"] = len(str(payload.get("prompt") or ""))
    elif event_type == "PostToolUse":
        event["tool_name"] = redact_text(payload.get("tool_name"))
        event["tool_use_id"] = hash_identifier(payload.get("tool_use_id"))
        event["outcome"] = safe_tool_outcome(payload.get("tool_response"))
    elif event_type in {"SubagentStart", "SubagentStop"}:
        event["agent_id"] = hash_identifier(payload.get("agent_id"))
        event["agent_type"] = redact_text(payload.get("agent_type"))
        report_path = os.environ.get("AI_SDL_REPORT_PATH")
        event["structured_report_reference_available"] = bool(report_path)
        event["structured_report_reference"] = hash_identifier(report_path)
        event["agent_transcript_reference_available"] = bool(payload.get("agent_transcript_path"))
        event["final_response_available"] = bool(payload.get("last_assistant_message"))
        event["final_response_captured"] = False
    return event


def main() -> int:
    if len(sys.argv) != 2:
        raise ValueError("Usage: log_hook_event.py <event-type>")
    payload = read_hook_input()
    event_type = sys.argv[1]
    append_event_best_effort(event_for(event_type, payload))
    if event_type in {"SubagentStart", "SubagentStop"}:
        print("{}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # Hook failures must be visible but contain no input echo.
        print(f"AI SDLC hook logging failed: {type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(1)
