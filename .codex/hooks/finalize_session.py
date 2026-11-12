"""Best-effort main-session finalization without reading transcript contents."""

from __future__ import annotations

import sys

from common import append_event_best_effort, base_event, read_hook_input


def main() -> int:
    payload = read_hook_input()
    event = base_event(payload, "SessionEnd")
    event["reason"] = payload.get("reason")
    event["transcript_available"] = bool(payload.get("transcript_path"))
    event["transcript_captured"] = False
    append_event_best_effort(event)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"AI SDLC session-finalization hook failed: {type(error).__name__}", file=sys.stderr)
        raise SystemExit(1)
