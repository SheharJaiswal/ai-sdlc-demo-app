# Tasks

## 1. Resolve implementation-bound decisions

- [x] 1.1 Record the product decision for the existing Admin role without assigning unapproved approval power; verify the decision is reflected in the implementation plan before changing authorization.
- [x] 1.2 Decide whether approval history is included in invoice responses or retained for enforcement/audit only; verify the selected contract is documented in the API-facing tests.

## 2. Model role-aware approval in the Domain

- [ ] 2.1 Add Domain representations for authenticated approver identity, Manager/Director role, and immutable approval-history entries; verify focused tests retain identity, role, and timestamp for accepted approvals.
- [ ] 2.2 Implement amount and role eligibility for 50,000, 50,001, 500,000, and 500,001; verify Manager and Director boundary tests and a Director 50,001 success test cover accepted and rejected outcomes.
- [ ] 2.3 Implement high-value first and second approval sequencing; verify first Manager/Director approval remains PendingApproval and only a distinct Director completes approval.
- [ ] 2.4 Validate all approval policy failures before mutation; verify each rejected attempt preserves invoice data, status, approval history, and timestamps while returning a clear reason.

## 3. Make approval persistence atomic

- [ ] 3.1 Extend the Domain repository contract with an atomic approval transition; verify the Domain service does not use separate read/validate/update operations for approval recording.
- [ ] 3.2 Implement the atomic transition in the in-memory repository; verify concurrent competing approvals cannot record a duplicate, invalid sequence, or invalid final status.
- [ ] 3.3 Update the fake repository for the atomic contract; verify approval-service tests use it without persistence-specific behavior leaking into Domain tests.

## 4. Align API authorization and behavior

- [ ] 4.1 Update authenticated session fixtures and approval authorization for the resolved Manager/Director role model; verify approval identity and role are server-derived and unauthenticated requests are denied.
- [ ] 4.2 Pass authenticated role-aware identity to Domain and preserve `ApiControllerBase.Handle` failure translation; verify API tests return meaningful policy failure responses and do not accept client-supplied approver identity or role.
- [ ] 4.3 Update invoice/API representation only if required by the resolved approval-history visibility decision; verify clients observe the selected contract.

## 5. Validate browser behavior and regression coverage

- [ ] 5.1 Add accessible page objects and Playwright scenarios for Manager, Director, high-value first/second approval, and visible failure feedback; verify locators use roles or labels only.
- [ ] 5.2 Add browser/API coverage that confirms rejected approvals leave displayed invoice status unchanged; verify no client path accesses persistence directly.
- [ ] 5.3 Run the configured Release build, unit tests, and Playwright suite; verify all results are recorded with any unavailable prerequisites explicitly noted.

## Workflow follow-up

- [ ] Review the completed change artifacts and implementation evidence before archiving this OpenSpec change.
