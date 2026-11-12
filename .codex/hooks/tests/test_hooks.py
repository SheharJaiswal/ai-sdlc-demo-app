from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

HOOKS = Path(__file__).resolve().parents[1]
HOOK_CONFIG = HOOKS.parent / "hooks.json"
sys.path.insert(0, str(HOOKS))

import finalize_session  # noqa: E402
import log_hook_event  # noqa: E402
import validate_on_stop  # noqa: E402
from common import redact_text  # noqa: E402
from validate_agent_report import validate_report  # noqa: E402

FIXTURES = HOOKS / "fixtures"


class HookTests(unittest.TestCase):
    def read_fixture(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def invoke(self, module, payload: dict, environment: dict[str, str] | None = None, arguments: list[str] | None = None) -> tuple[int, str]:
        output = io.StringIO()
        old_stdin = sys.stdin
        old_argv = sys.argv
        try:
            sys.stdin = io.StringIO(json.dumps(payload))
            sys.argv = [module.__file__, *(arguments or [])]
            with patch.dict(os.environ, environment or {}, clear=False), redirect_stdout(output):
                result = module.main()
        finally:
            sys.stdin = old_stdin
            sys.argv = old_argv
        return result, output.getvalue()

    def test_prompt_redaction(self) -> None:
        text = redact_text('password=secret-value Authorization: Bearer token-value sk-example')
        self.assertNotIn("secret-value", text)
        self.assertNotIn("token-value", text)
        self.assertNotIn("sk-example", text)
        self.assertIn("[REDACTED]", text)

    def test_prompt_logging_records_length_without_persisting_prompt_text(self) -> None:
        prompt = "synthetic password is test-secret-123"

        event = log_hook_event.event_for(
            "UserPromptSubmit",
            {"session_id": "session", "turn_id": "turn", "prompt": prompt},
        )

        self.assertEqual(len(prompt), event["prompt_length"])
        self.assertNotIn("prompt", event)
        self.assertNotIn(prompt, json.dumps(event))

    def test_hook_configuration_uses_supported_windows_commands(self) -> None:
        """Codex recognizes `windows`; `commandWindows` is not a hook property."""
        configured = json.loads(HOOK_CONFIG.read_text(encoding="utf-8"))["hooks"]
        expected_events = {
            "UserPromptSubmit", "PostToolUse", "SubagentStart",
            "SubagentStop", "Stop", "SessionEnd",
        }
        self.assertEqual(expected_events, set(configured))
        for event_name, matchers in configured.items():
            with self.subTest(event_name=event_name):
                command = matchers[0]["hooks"][0]
                self.assertIn("windows", command)
                self.assertNotIn("commandWindows", command)
                self.assertNotIn("git rev-parse", command["command"])
                self.assertNotIn("git rev-parse", command["windows"])
                self.assertTrue(command["windows"].startswith("py -3 .codex/hooks/"))

    def test_noncritical_log_io_failure_is_visible_without_failing_hook(self) -> None:
        output = io.StringIO()
        error_output = io.StringIO()
        old_stdin = sys.stdin
        old_argv = sys.argv
        try:
            sys.stdin = io.StringIO('{"session_id":"s"}')
            sys.argv = [log_hook_event.__file__, "UserPromptSubmit"]
            with patch.object(log_hook_event, "append_event_best_effort", return_value=False), redirect_stdout(output), redirect_stderr(error_output):
                self.assertEqual(0, log_hook_event.main())
        finally:
            sys.stdin = old_stdin
            sys.argv = old_argv

    def test_best_effort_logging_reports_os_error(self) -> None:
        from common import append_event_best_effort

        error_output = io.StringIO()
        with patch("common.append_event", side_effect=OSError("denied")), redirect_stderr(error_output):
            self.assertFalse(append_event_best_effort({"event_type": "test"}))
        self.assertIn("AI SDLC hook logging unavailable: OSError", error_output.getvalue())

    def test_redacts_common_provider_tokens_and_multiline_private_keys(self) -> None:
        samples = [
            "ghp_abcdefghijklmnopqrstuvwxyz123456",
            "github_pat_abcdefghijklmnopqrstuvwxyz_1234567890",
            "AKIA1234567890ABCDEF",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signaturepayload",
            "password: two words with spaces",
            "-----BEGIN PRIVATE KEY-----\\nsynthetic-private-key-material\\n-----END PRIVATE KEY-----",
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                redacted = redact_text(sample)
                self.assertNotIn(sample, redacted)
                self.assertIn("[REDACTED", redacted)

    def test_log_file_permissions_are_owner_only_where_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "events.jsonl"
            self.invoke(log_hook_event, {"session_id": "s"}, {"AI_SDL_LOG_PATH": str(log)}, ["UserPromptSubmit"])
            if os.name == "posix":
                self.assertEqual(0o600, log.stat().st_mode & 0o777)

    def test_tool_metadata_logging_excludes_response(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "events.jsonl"
            payload = {"session_id": "session", "turn_id": "turn", "tool_name": "Bash", "tool_response": "password=never-log"}
            result, _ = self.invoke(log_hook_event, payload, {"AI_SDL_LOG_PATH": str(log)}, ["PostToolUse"])
            self.assertEqual(0, result)
            event = json.loads(log.read_text(encoding="utf-8"))
            self.assertEqual("PostToolUse", event["event_type"])
            self.assertEqual("Bash", event["tool_name"])
            self.assertNotIn("never-log", json.dumps(event))

    def test_subagent_start_and_stop_logging(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "events.jsonl"
            environment = {"AI_SDL_LOG_PATH": str(log)}
            self.assertEqual(0, self.invoke(log_hook_event, {"session_id": "s", "turn_id": "t", "agent_id": "a", "agent_type": "qa"}, environment, ["SubagentStart"])[0])
            self.assertEqual(0, self.invoke(log_hook_event, {"session_id": "s", "turn_id": "t", "agent_id": "a", "agent_type": "qa", "last_assistant_message": "done"}, environment, ["SubagentStop"])[0])
            events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(["SubagentStart", "SubagentStop"], [event["event_type"] for event in events])
            self.assertEqual("{}", self.invoke(log_hook_event, {"session_id": "s"}, environment, ["SubagentStop"])[1].strip())
            self.assertTrue(events[1]["final_response_available"])
            self.assertFalse(events[1]["final_response_captured"])

    def test_session_finalization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "events.jsonl"
            result, _ = self.invoke(finalize_session, {"session_id": "s", "reason": "other", "transcript_path": "/private/transcript"}, {"AI_SDL_LOG_PATH": str(log)})
            self.assertEqual(0, result)
            event = json.loads(log.read_text(encoding="utf-8"))
            self.assertEqual("SessionEnd", event["event_type"])
            self.assertTrue(event["transcript_available"])
            self.assertFalse(event["transcript_captured"])

    def test_valid_structured_report(self) -> None:
        self.assertEqual([], validate_report(self.read_fixture("valid-report.json")))

    def test_missing_required_field(self) -> None:
        errors = validate_report(self.read_fixture("missing-required-field.json"))
        self.assertTrue(any("payload" in error for error in errors))

    def test_invalid_report_type(self) -> None:
        errors = validate_report(self.read_fixture("invalid-report-type.json"))
        self.assertTrue(any("report_type" in error for error in errors))

    def test_invalid_status(self) -> None:
        errors = validate_report(self.read_fixture("invalid-status.json"))
        self.assertTrue(any("status" in error for error in errors))

    def test_invalid_finding_severity(self) -> None:
        errors = validate_report(self.read_fixture("invalid-finding-severity.json"))
        self.assertTrue(any("severity" in error for error in errors))

    def test_stop_does_not_block_without_report_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "events.jsonl"
            result, output = self.invoke(validate_on_stop, {"session_id": "s", "turn_id": "t", "stop_hook_active": False}, {"AI_SDL_LOG_PATH": str(log)})
            self.assertEqual(0, result)
            self.assertEqual("{}", output.strip())

    def test_stop_accepts_valid_requested_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "events.jsonl"
            report = Path(directory) / "report.json"
            report.write_text(json.dumps(self.read_fixture("valid-report.json")), encoding="utf-8")
            result, output = self.invoke(
                validate_on_stop,
                {"session_id": "s", "turn_id": "t", "stop_hook_active": False},
                {"AI_SDL_LOG_PATH": str(log), "AI_SDL_REQUIRE_REPORT": "1", "AI_SDL_REPORT_PATH": str(report)},
            )
            self.assertEqual(0, result)
            self.assertEqual("{}", output.strip())

    def test_stop_blocks_invalid_requested_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "events.jsonl"
            report = Path(directory) / "report.json"
            invalid = self.read_fixture("valid-report.json")
            invalid["unexpected"] = "not allowed"
            report.write_text(json.dumps(invalid), encoding="utf-8")
            result, output = self.invoke(
                validate_on_stop,
                {"session_id": "s", "turn_id": "t", "stop_hook_active": False},
                {"AI_SDL_LOG_PATH": str(log), "AI_SDL_REQUIRE_REPORT": "1", "AI_SDL_REPORT_PATH": str(report)},
            )
            self.assertEqual(0, result)
            self.assertIn('"decision": "block"', output)

    def test_stop_reports_missing_requested_report_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "events.jsonl"
            result, output = self.invoke(validate_on_stop, {"session_id": "s", "turn_id": "t", "stop_hook_active": False}, {"AI_SDL_LOG_PATH": str(log), "AI_SDL_REQUIRE_REPORT": "1"})
            self.assertEqual(0, result)
            self.assertIn('"decision": "block"', output)
            result, output = self.invoke(validate_on_stop, {"session_id": "s", "turn_id": "t", "stop_hook_active": True}, {"AI_SDL_LOG_PATH": str(log), "AI_SDL_REQUIRE_REPORT": "1"})
            self.assertEqual(0, result)
            self.assertIn("systemMessage", output)


    def test_report_rejects_unexpected_root_property(self) -> None:
        report = self.read_fixture("valid-report.json")
        report["unexpected"] = "not allowed"
        self.assertTrue(any("unsupported properties" in error for error in validate_report(report)))

    def test_report_rejects_invalid_evidence_kind(self) -> None:
        report = self.read_fixture("valid-report.json")
        report["evidence"][0]["kind"] = "made_up"
        self.assertTrue(any("evidence[0].kind" in error for error in validate_report(report)))

    def test_report_rejects_datetime_without_timezone(self) -> None:
        report = self.read_fixture("valid-report.json")
        report["generated_at"] = "2026-11-12T00:00:00"
        self.assertTrue(any("timezone" in error for error in validate_report(report)))

    def test_report_rejects_non_string_array_items(self) -> None:
        report = self.read_fixture("valid-report.json")
        report["risks"] = [123]
        self.assertTrue(any("risks[0]" in error for error in validate_report(report)))

    def test_report_rejects_unexpected_nested_properties(self) -> None:
        report = self.read_fixture("valid-report.json")
        report["evidence"][0]["extra"] = True
        self.assertTrue(any("evidence[0] contains unsupported" in error for error in validate_report(report)))


if __name__ == "__main__":
    unittest.main()
