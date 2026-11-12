"""Validate agent reports against the repository's JSON Schema contract.

The implementation is standard-library-only. It enforces the constraints used by
agent-report.schema.json; keep the two definitions synchronized when the schema changes.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

REPORT_TYPES = {"business_analysis", "architecture", "developer_handoff", "qa", "security", "code_review"}
STATUSES = {"complete", "blocked", "needs_decision"}
SEVERITIES = {"critical", "high", "medium", "low", "info"}
EVIDENCE_KINDS = {"file", "command", "test", "document", "diff"}
EVIDENCE_RESULTS = {"pass", "fail", "not_run", "observed"}

ROOT_FIELDS = {
    "schema_version", "report_type", "report_id", "session_id", "agent", "status",
    "summary", "evidence", "findings", "risks", "decisions_needed", "validation",
    "payload", "generated_at",
}
AGENT_FIELDS = {"name", "version"}
VALIDATION_FIELDS = {"commands_executed", "commands_not_run"}
EVIDENCE_FIELDS = {"kind", "reference", "result"}
FINDING_FIELDS = {"id", "severity", "summary", "evidence", "recommendation"}
REQUIRED_FIELDS = ROOT_FIELDS


def _require_object(value: Any, path: str, errors: list[str]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{path} must be an object.")
        return None
    return value


def _check_properties(value: dict[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        errors.append(f"{path} contains unsupported properties: {', '.join(unexpected)}.")


def _require_string(value: Any, path: str, errors: list[str], nonempty: bool = False) -> None:
    if not isinstance(value, str):
        errors.append(f"{path} must be a string.")
    elif nonempty and not value.strip():
        errors.append(f"{path} must not be empty.")


def _require_string_array(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array.")
        return
    for index, item in enumerate(value):
        _require_string(item, f"{path}[{index}]", errors)


def _require_list(value: Any, path: str, errors: list[str]) -> list[Any] | None:
    if not isinstance(value, list):
        errors.append(f"{path} must be an array.")
        return None
    return value


def _validate_datetime(value: Any, errors: list[str]) -> None:
    path = "generated_at"
    _require_string(value, path, errors, nonempty=True)
    if not isinstance(value, str) or not value.strip():
        return
    # RFC 3339 date-time requires an explicit UTC marker or numeric offset.
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})",
        value,
    ):
        errors.append("generated_at must be an RFC-3339 date-time with an explicit timezone.")
        return
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            errors.append("generated_at must include a timezone.")
    except ValueError:
        errors.append("generated_at must be a valid RFC-3339 date-time.")


def _validate_evidence(value: Any, path: str, errors: list[str]) -> None:
    item = _require_object(value, path, errors)
    if item is None:
        return
    _check_properties(item, EVIDENCE_FIELDS, path, errors)
    missing = sorted(EVIDENCE_FIELDS - set(item))
    if missing:
        errors.append(f"{path} is missing required properties: {', '.join(missing)}.")
    if item.get("kind") not in EVIDENCE_KINDS:
        errors.append(f"{path}.kind must be one of: {', '.join(sorted(EVIDENCE_KINDS))}.")
    _require_string(item.get("reference"), f"{path}.reference", errors, nonempty=True)
    if item.get("result") not in EVIDENCE_RESULTS:
        errors.append(f"{path}.result must be one of: {', '.join(sorted(EVIDENCE_RESULTS))}.")


def validate_report(report: Any) -> list[str]:
    errors: list[str] = []
    root = _require_object(report, "report", errors)
    if root is None:
        return errors

    _check_properties(root, ROOT_FIELDS, "report", errors)
    missing = sorted(REQUIRED_FIELDS - set(root))
    if missing:
        errors.append("Missing required fields: " + ", ".join(missing) + ".")

    if root.get("schema_version") != "1.0":
        errors.append("schema_version must equal '1.0'.")
    if root.get("report_type") not in REPORT_TYPES:
        errors.append("report_type must be one of: " + ", ".join(sorted(REPORT_TYPES)) + ".")
    if root.get("status") not in STATUSES:
        errors.append("status must be one of: " + ", ".join(sorted(STATUSES)) + ".")

    for field in ("report_id", "session_id"):
        _require_string(root.get(field), field, errors, nonempty=True)
    _require_string(root.get("summary"), "summary", errors)
    _validate_datetime(root.get("generated_at"), errors)

    agent = _require_object(root.get("agent"), "agent", errors)
    if agent is not None:
        _check_properties(agent, AGENT_FIELDS, "agent", errors)
        missing_agent = sorted(AGENT_FIELDS - set(agent))
        if missing_agent:
            errors.append("agent is missing required properties: " + ", ".join(missing_agent) + ".")
        _require_string(agent.get("name"), "agent.name", errors, nonempty=True)
        _require_string(agent.get("version"), "agent.version", errors, nonempty=True)

    evidence = _require_list(root.get("evidence"), "evidence", errors)
    if evidence is not None:
        for index, item in enumerate(evidence):
            _validate_evidence(item, f"evidence[{index}]", errors)

    findings = _require_list(root.get("findings"), "findings", errors)
    if findings is not None:
        for index, item in enumerate(findings):
            path = f"findings[{index}]"
            finding = _require_object(item, path, errors)
            if finding is None:
                continue
            _check_properties(finding, FINDING_FIELDS, path, errors)
            required_finding = FINDING_FIELDS - {"recommendation"}
            missing_finding = sorted(required_finding - set(finding))
            if missing_finding:
                errors.append(f"{path} is missing required properties: {', '.join(missing_finding)}.")
            _require_string(finding.get("id"), f"{path}.id", errors, nonempty=True)
            if finding.get("severity") not in SEVERITIES:
                errors.append(f"{path}.severity must be one of: " + ", ".join(sorted(SEVERITIES)) + ".")
            _require_string(finding.get("summary"), f"{path}.summary", errors, nonempty=True)
            finding_evidence = _require_list(finding.get("evidence"), f"{path}.evidence", errors)
            if finding_evidence is not None:
                for evidence_index, evidence_item in enumerate(finding_evidence):
                    _validate_evidence(evidence_item, f"{path}.evidence[{evidence_index}]", errors)
            if "recommendation" in finding:
                _require_string(finding["recommendation"], f"{path}.recommendation", errors)

    _require_string_array(root.get("risks"), "risks", errors)
    _require_string_array(root.get("decisions_needed"), "decisions_needed", errors)

    validation = _require_object(root.get("validation"), "validation", errors)
    if validation is not None:
        _check_properties(validation, VALIDATION_FIELDS, "validation", errors)
        missing_validation = sorted(VALIDATION_FIELDS - set(validation))
        if missing_validation:
            errors.append("validation is missing required properties: " + ", ".join(missing_validation) + ".")
        _require_string_array(validation.get("commands_executed"), "validation.commands_executed", errors)
        _require_string_array(validation.get("commands_not_run"), "validation.commands_not_run", errors)

    _require_object(root.get("payload"), "payload", errors)
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_agent_report.py <report.json>", file=sys.stderr)
        return 2
    try:
        report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Unable to read report: {error}", file=sys.stderr)
        return 2
    errors = validate_report(report)
    if errors:
        print("Agent report validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Agent report is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
