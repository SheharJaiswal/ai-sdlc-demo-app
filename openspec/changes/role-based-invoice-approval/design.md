# Design

## Context

See [proposal.md](proposal.md) for motivation and [invoice-approval spec](specs/invoice-approval/spec.md) for behavior. The current Domain service performs a one-step approval using only an approver string. The repository exposes separate reads and updates, and the API authorizes generic `Approver` and `Admin` roles.

## Goals / Non-Goals

**Goals:**

- Keep policy evaluation and validation in the Domain layer.
- Preserve authenticated identity and approval history needed for the two-person rule.
- Make validation and persistence of one approval atomic in the configured in-memory repository.
- Preserve the existing controller error-handling convention while exposing meaningful policy failures.

**Non-Goals:**

- Introducing a database, distributed workflow, or external identity provider.
- Defining approval powers for roles other than Manager and Director.
- Changing invoice submission or generic rejection rules beyond integration needed for approval history integrity.
- Exposing approval history in a new API or UI unless that is resolved before implementation.

## Decisions

### Domain policy uses authenticated identity and role

Represent the approver passed into the Domain service as a value that contains stable authenticated identity and role. The API obtains both values from the server-side session; the browser does not submit either. The Domain service evaluates amount, role, existing history, and invoice status before mutation.

This keeps authorization eligibility and business policy testable outside HTTP. Passing only a username is rejected because it cannot enforce role rules. Controller-side policy checks are rejected because they would duplicate business rules and bypass the Domain boundary.

### Approval history is immutable Domain state

Add approval records sufficient to retain authenticated identity, the role used for the decision, and the decision timestamp. For high-value invoices, the service appends a first valid record without changing the status, and appends the second record only when it is from a distinct Director.

Storing a single replacement `DecidedBy` value is rejected because it cannot prove or enforce the two-person policy. The exact public representation of history remains open; the Domain representation is required.

### Repository transition is atomic

Extend the Domain repository contract with an operation that performs lookup, validation callback/policy evaluation, history update, and persistence under one repository-controlled critical section for an invoice. The in-memory implementation owns synchronization; callers do not lock controllers or static process-wide objects.

Separate `GetById` and `Update` operations are rejected for approval processing because concurrent calls can both observe the same pending state. The transition must ensure any failed policy validation commits no changes.

### Admin remains outside the approval policy

The existing Admin role has no approval authority. The approved policy grants approval to Managers and Directors only, so Admin is not mapped to either role. Integration coverage confirms an Admin cannot call the approval endpoint.

### Approval history is returned to authenticated invoice clients

The invoice response includes `approvalHistory` with identity, role, and approval timestamp. The UI uses it to show approval progress, and the Domain uses it to enforce distinct identities and the Director-only second approval. The existing authenticated invoice response is retained rather than introducing a separate audit endpoint.

### API authorization and error translation remain boundary concerns

Approval endpoints require the policy roles at the API boundary and obtain approver details from the authenticated session. Domain policy failures retain a clear reason and pass through `ApiControllerBase.Handle` using its established expected-failure mapping. Requests must not include an approver identifier or role field.

### Verification is layered

Domain tests cover boundaries, role eligibility, history, immutable failures, and deterministic concurrency. API tests cover authenticated identity, authorization, and error translation. Playwright tests use page objects and accessible locators for role-specific approval feedback and state preservation.

## Risks / Trade-offs

- [Mutable in-memory entities can escape repository synchronization] -> The atomic transition must control the approval mutation and repository persistence path; tests must exercise competing requests.
- [Role changes could be confused with a second identity] -> Distinctness is evaluated by stable authenticated user identity, not role or request shape.
- [History representation could expose more data than needed] -> Keep the public response shape undecided; retain only policy-required identity/role/timestamp data in Domain history.
- [Existing Admin behavior is unspecified] -> Block implementation of Admin approval semantics until a product decision is recorded.

## Migration Plan

1. Add the Domain approval-history and role-aware policy model with focused tests.
2. Add the atomic repository transition and in-memory implementation tests.
3. Align authenticated session fixtures and API authorization with the resolved role decision.
4. Update API/UI behavior and add browser tests.
5. Run the configured build, unit, and Playwright verification before release.

Rollback is code rollback to the current single-approver behavior; no persistent data migration is required because the configured store is in-memory.

## Resolved Questions

- Admin remains an operational role without approval authority.
- Approval history is returned in existing authenticated invoice responses and is used by the UI and Domain policy.
- Approval records contain the identity, role, and timestamp needed by the policy; no additional classification is required.
