---
name: dotnet-domain-development
description: Implement small, domain-first .NET changes with explicit validation, repository boundaries, and focused tests.
---

# .NET domain development

## When to use

Use when implementing an approved .NET/OpenSpec task that changes domain behavior, persistence abstractions, or API wiring.

## Expected input

- Approved OpenSpec task or explicit implementation authorization.
- AGENTS.md, impacted source, and existing tests.

## Instructions

1. Put business policy and validation in the Domain project.
2. Keep controllers focused on HTTP/authentication and repositories behind Domain interfaces.
3. Prefer small focused methods, explicit validation before mutation, and clear domain errors.
4. Preserve atomicity when a decision requires read-modify-write behavior.
5. Add xUnit tests using existing repository conventions and test observable outcomes.
6. Keep changes scoped; do not commit or push automatically.

## Expected output

Developer-handoff JSON describing changed files, policy behavior, tests, and commands actually run.

## Quality checklist

- No business logic in controllers or `Program.cs`.
- Rejected paths do not mutate state.
- Tests cover positive, negative, and boundary behavior.
- No unrelated edits.
