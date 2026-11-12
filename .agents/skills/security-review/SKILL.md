---
name: security-review
description: Review authorization, identity, concurrency, sensitive logging, and audit integrity without modifying code.
---

# Security review

## When to use

Use before approval of an authentication, authorization, approval-workflow, logging, or persistence change.

## Expected input

- AGENTS.md, change diff/design, authorization code, and tests.

## Instructions

1. Verify role checks are server-side and cannot be bypassed by UI input.
2. Trace approver identity from authentication through persistence.
3. Assess duplicate identity, role changes, replay, and concurrent-request risks.
4. Check logs and audit records for secret or sensitive-data exposure.
5. Classify findings by severity and provide evidence and verification steps.

## Expected output

Structured security JSON; findings only, with no automatic fixes.

## Quality checklist

- Distinguish verified findings from hypotheses.
- Include authorization and concurrency checks.
- Never expose secrets in reports.
