# Proposal

## Why

The current invoice workflow approves every pending invoice with one generic approver and cannot enforce the approved amount- and role-based approval policy. High-value invoices need an auditable, atomic two-person approval flow so that authorization and invoice state remain correct under rejected and concurrent requests.

## What Changes

- Add role-aware approval policy for authenticated Managers and Directors using the inclusive 50,000 and 500,000 amount boundaries.
- Record sufficient approval history to enforce distinct approvers and a Director-only second approval for invoices above 500,000.
- Keep high-value invoices pending after the first valid approval and approve them only after a distinct Director supplies the second valid approval.
- Enforce all approval decisions atomically at the repository boundary and preserve invoice state after rejected attempts.
- Align approval API authorization and error behavior with the policy while retaining server-derived approver identity.
- Add Domain, API, concurrency, and browser acceptance coverage for valid and rejected policy paths.

## Capabilities

### New Capabilities

- `invoice-approval`: Role- and amount-based invoice approval, approval-history integrity, and observable API behavior.

### Modified Capabilities

None. No existing OpenSpec capability specifications are present.

## Impact

- Domain: `Invoice`, `ApprovalService`, and `IInvoiceRepository` require role-aware approval and atomic-transition support.
- API: authentication fixtures/authorization, approval endpoints, error mapping, and invoice representations may require updates.
- Persistence: `InMemoryInvoiceRepository` must preserve approval history and provide the configured atomic transition.
- UI and tests: approval feedback and role-based workflows require unit, API, concurrency, and Playwright coverage.
- No new external dependency is proposed.
