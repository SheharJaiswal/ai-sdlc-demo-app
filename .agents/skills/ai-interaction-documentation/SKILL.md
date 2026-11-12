---
name: ai-interaction-documentation
description: Produce structured agent reports and sanitized AI-assisted SDLC evidence without capturing secrets or private reasoning.
---

# AI interaction documentation

## When to use

Use when an agent must create a structured handoff/report or document AI-assisted SDLC evidence.

## Expected input

- Applicable report type, evidence, commands executed, and known limitations.

## Instructions

1. Use the common agent-report schema when a structured report is requested.
2. Record only evidence references, sanitized summaries, timestamps, and hashed/redacted session identifiers.
3. Never include passwords, API keys, tokens, authorization headers, private environment values, unrestricted transcripts, or chain-of-thought.
4. State commands actually executed and explicitly list important commands not run.
5. Preserve uncertainty and blockers rather than fabricating success.

## Expected output

Schema-valid report JSON and, when requested, sanitized Markdown evidence.

## Quality checklist

- All required envelope fields are present.
- Evidence is reproducible and non-sensitive.
- No historical activity is invented.
