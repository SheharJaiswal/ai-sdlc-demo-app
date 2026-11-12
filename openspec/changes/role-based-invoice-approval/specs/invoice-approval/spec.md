# Spec Delta

## Purpose

Defines role- and amount-based invoice approval that preserves approval integrity, history, and consistent observable outcomes for authenticated users.

## ADDED Requirements

### Requirement: Role- and amount-based approval eligibility
The system SHALL approve a pending invoice in one decision when a Manager approves an amount at or below 50,000, or when a Director approves an amount at or below 500,000. A Manager SHALL be rejected for an amount above 50,000 unless acting as the first approver of an invoice above 500,000.

#### Scenario: Manager approves the inclusive lower boundary
- **WHEN** an authenticated Manager approves a pending invoice with amount 50,000
- **THEN** the invoice becomes Approved with the approval recorded

#### Scenario: Manager is rejected above the lower boundary
- **WHEN** an authenticated Manager approves a pending invoice with amount 50,001
- **THEN** the attempt is rejected with a clear business reason and the invoice remains unchanged

#### Scenario: Director approves within the Director-only range
- **WHEN** an authenticated Director approves a pending invoice with amount 50,001
- **THEN** the invoice becomes Approved with the approval recorded

#### Scenario: Director approves the inclusive upper single-approval boundary
- **WHEN** an authenticated Director approves a pending invoice with amount 500,000
- **THEN** the invoice becomes Approved with the approval recorded

### Requirement: High-value invoices require two distinct approvals
The system SHALL require two approvals for a pending invoice with amount above 500,000. The first approval SHALL be accepted from a Manager or Director and recorded while the invoice remains PendingApproval. The second approval SHALL be accepted only from a Director whose authenticated identity differs from the first approver, after which the invoice SHALL become Approved.

#### Scenario: Valid first Manager approval remains pending
- **WHEN** an authenticated Manager first approves a pending invoice with amount 500,001
- **THEN** the approval is recorded and the invoice remains PendingApproval

#### Scenario: Valid first Director approval remains pending
- **WHEN** an authenticated Director first approves a pending invoice with amount above 500,000
- **THEN** the approval is recorded and the invoice remains PendingApproval

#### Scenario: Distinct Director provides the second approval
- **WHEN** a Director with a different authenticated identity approves an invoice above 500,000 after one valid first approval
- **THEN** the second approval is recorded and the invoice becomes Approved

#### Scenario: Invalid second approver is rejected
- **WHEN** the same authenticated user or a non-Director attempts the second approval of an invoice above 500,000
- **THEN** the attempt is rejected with a clear business reason and the invoice remains PendingApproval

### Requirement: Approval identity and rejection immutability
The system SHALL retain approval history sufficient to prevent the same authenticated user from counting as two approvers, including when role or request details differ. Before rejecting an approval attempt, the system SHALL validate the policy without changing invoice data, status, approval history, or timestamps.

#### Scenario: Same user cannot approve twice under a changed role context
- **WHEN** a user who supplied the first high-value approval attempts another approval with a different role context or request
- **THEN** the attempt is rejected and no invoice state, approval history, or timestamp changes

#### Scenario: Policy rejection preserves all invoice state
- **WHEN** any approval attempt violates the amount, role, identity, or sequence policy
- **THEN** the response provides a clear business reason and the invoice data, status, approval history, and timestamps are unchanged

### Requirement: Atomic approval processing
The system SHALL atomically validate and record an approval at the configured repository boundary so concurrent requests cannot bypass approval sequence, role, or distinct-identity requirements.

#### Scenario: Concurrent approvals preserve a valid outcome
- **WHEN** concurrent approval requests target the same pending invoice
- **THEN** the recorded approval history and invoice status satisfy the approval policy and each rejected request leaves state unchanged

### Requirement: Authenticated approval API behavior
The approval API SHALL derive approver identity and role from the authenticated server-side session rather than client-supplied approver data. It SHALL require sign-in for approval actions and return meaningful domain failure responses through the existing API error-handling convention.

#### Scenario: Unauthenticated approval is denied
- **WHEN** an unauthenticated client attempts an approval action
- **THEN** the API denies the request without recording an approval

#### Scenario: Policy failure is returned to the client
- **WHEN** an authenticated approval action violates the policy
- **THEN** the API returns the clear business reason and no approval is recorded
