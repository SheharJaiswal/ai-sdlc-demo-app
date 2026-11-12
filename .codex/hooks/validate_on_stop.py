"""Validate a report only when the invoking task explicitly requests one."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from common import append_event_best_effort, base_event, read_hook_input
from validate_agent_report import validate_report


def main() -> int:
    payload = read_hook_input()
    event = base_event(payload, "Stop")
    required = os.environ.get("AI_SDL_REQUIRE_REPORT") == "1"
    report_path = os.environ.get("AI_SDL_REPORT_PATH")
    event["report_required"] = required
    event["report_path_configured"] = bool(report_path)
    errors: list[str] = []
    if required:
        if not report_path:
            errors.append("AI_SDL_REPORT_PATH is required when AI_SDL_REQUIRE_REPORT=1.")
        else:
            try:
                report = json.loads(Path(report_path).read_text(encoding="utf-8"))
                errors.extend(validate_report(report))
            except (OSError, json.JSONDecodeError) as error:
                errors.append(f"Unable to read structured report: {error}")
    event["report_valid"] = required and not errors if required else None
    event["validation_error_count"] = len(errors)
    append_event_best_effort(event)
    if not errors:
        print("{}")
        return 0
    message = "Structured report validation failed: " + " ".join(errors[:3])
    if payload.get("stop_hook_active"):
        print(json.dumps({"systemMessage": message}))
    else:
        print(json.dumps({"decision": "block", "reason": message}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"systemMessage": f"Structured report hook failed: {type(error).__name__}"}))
        raise SystemExit(1)
