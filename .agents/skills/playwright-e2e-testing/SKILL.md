---
name: playwright-e2e-testing
description: Create and review accessible Playwright end-to-end tests with page objects and evidence-based assertions.
---

# Playwright E2E testing

## When to use

Use for approved browser-flow testing, especially invoice approval and rejected-action behavior.

## Expected input

- AGENTS.md, UI/API behavior, and the relevant page objects/tests.

## Instructions

1. Use page objects under `e2e/pages` and tests under `e2e/tests`.
2. Use `getByRole` and `getByLabel`; never CSS or XPath selectors.
3. Assert user-visible outcomes and state preservation after rejected actions.
4. Create data through supported UI/API flows and isolate test state.
5. Record prerequisites, commands, and actual results.

## Expected output

Structured QA report with covered scenarios, evidence, failures, and unrun tests.

## Quality checklist

- Rejection message is asserted.
- Invoice status and visible state are asserted after rejection.
- No brittle selectors or arbitrary waits.
- Browser/setup limitations are reported honestly.
