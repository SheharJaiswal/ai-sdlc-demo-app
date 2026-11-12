# AI in SDLC assignment write-up

## Feature delivered

Role-based invoice approval limits are implemented in the Domain service. Managers and Directors can independently approve invoices up to 50,000; only Directors can independently approve invoices above 50,000 through 500,000. Invoices above 500,000 require a first Manager or Director approval and a second approval from a different Director. Approval decisions are atomic at the in-memory repository boundary. Rejected decisions return a business reason and do not mutate invoice state.

## Commit order

1. `263694b docs: specify role-based invoice approval` — OpenSpec proposal, design, policy spec, and task breakdown.
2. `f414ff0 feat: enforce single-approver role limits` — Manager/Director limits, server-derived approval identity, rejection behavior, unit/API coverage, and the over-limit browser test.
3. `60bede1 feat: require distinct director approval for high-value invoices` — two-approver workflow, distinct-identity enforcement, atomicity/concurrency coverage, and browser progress for high-value approvals.

## Verification

| Check | Result |
|---|---|
| Release build | Passed; 0 warnings and 0 errors |
| .NET tests | Passed; 16 tests |
| Playwright | Passed; 2 tests |
| Hook tests | Passed; 24 tests |
| Stryker.NET 4.13.0 baseline | 30.77% |
| Stryker.NET 4.13.0 final | 55.41% (41 killed, 5 survived, 46 tested) |

The Stryker runs used Release configuration against the Domain project with the `InvoiceApp.Tests` project. The run was cleaned before the final measurement to avoid stale Release intermediates.

## Review findings and verdicts

An independent review of the implementation found these two medium-severity issues. Both were fixed and confirmed resolved in follow-up review:

1. **Fixed — prompt privacy:** the interaction hook previously retained prompt bodies. It now stores prompt length only; the hook regression suite verifies that prompt text is not logged.
2. **Fixed — atomic rejection:** rejection validation and updates previously did not share the repository's atomic transition. Approval and rejection now transition under the same repository lock, with a concurrent approve/reject regression test.

These are local independent-review findings, not findings from the workshop's required review prompt against a published pull request. The workshop review and final PR description are still pending.

## Required external handoff

- **Pull request:** pending. Open the PR from the assignment fork, run the workshop review prompt against that PR diff, and include every finding with a `fixed`, `dismissed with reason`, or `deferred with reason` verdict.
- **Demo video:** pending. Record and upload an 8–10 minute MP4 showing a live test or mutation run, then replace this line with the video URL.

The implementation branch is locally verified. PR creation and video recording/upload require GitHub write access and a screen recorder/account not available in this workspace session.
