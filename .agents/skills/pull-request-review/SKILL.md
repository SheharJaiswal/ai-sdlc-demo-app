---
name: pull-request-review
description: Independently review code changes for correctness, policy compliance, regression risk, and test quality.
---

# Pull request review

## When to use

Use after an implementation increment is available for review.

## Expected input

- Base branch, change diff, AGENTS.md, relevant tests, and developer handoff.

## Instructions

1. Inspect the diff before drawing conclusions.
2. Prioritize correctness, security, regression risk, and missing tests over style.
3. Classify findings as critical, high, medium, low, or info.
4. Cite files/symbols and provide reproduction or verification steps where possible.
5. Do not fix findings automatically.

## Expected output

Structured code-review JSON with findings, evidence, verdict, and remaining risks.

## Quality checklist

- Findings are actionable and evidence-based.
- Policy compliance and negative paths are reviewed.
- Passing tests are not treated as proof of complete coverage.
