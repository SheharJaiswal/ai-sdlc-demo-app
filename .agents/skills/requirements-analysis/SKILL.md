---
name: requirements-analysis
description: Extract, clarify, and trace software requirements before implementation or specification work.
---

# Requirements analysis

## When to use

Use for a new feature, policy change, ambiguous request, or before an OpenSpec proposal.

## Expected input

- User request and approved decisions.
- AGENTS.md and relevant source/documents.

## Instructions

1. Separate stated facts from assumptions.
2. Identify actors, behaviors, constraints, data invariants, and non-functional requirements.
3. Identify ambiguities that need an engineering-lead decision; do not silently resolve material ambiguity.
4. Derive positive, negative, boundary, and concurrency scenarios.
5. Produce a traceability matrix mapping each requirement to acceptance criteria and planned tests.

## Expected output

Structured business-analysis JSON or a concise report containing requirements, ambiguities, acceptance criteria, scenarios, evidence, and decisions needed.

## Quality checklist

- Every requirement has an observable acceptance criterion.
- Boundary values and rejected paths are explicit.
- Assumptions are labeled.
- No implementation is performed.
