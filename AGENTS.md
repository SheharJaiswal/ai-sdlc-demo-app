# Engineering context for AI agents

## Project overview

Invoice Approval Demo App is a deliberately small invoice workflow application used for AI-in-SDLC demonstrations. It has an ASP.NET Core .NET 8 Web API, a static browser UI, and an in-memory data store; it does not use a database.

Technology stack:

- Backend: C# and ASP.NET Core, targeting `net8.0`.
- Frontend: static HTML, CSS, and browser JavaScript, served from the API project.
- Unit tests: xUnit with `Microsoft.NET.Test.Sdk` and Coverlet collector.
- End-to-end tests: Playwright with Chromium.
- CI: GitHub Actions.

## Architecture and layering

- `backend/src/InvoiceApp.Domain`: domain entities, repository abstractions, and business rules. `ApprovalService` owns the invoice lifecycle: `Draft`, `PendingApproval`, `Approved`, and `Rejected`. This project must not depend on HTTP, UI, or storage implementation concerns.
- `backend/src/InvoiceApp.Api`: HTTP controllers, sign-in and session authentication under `Auth/`, the in-memory repository implementation, dependency registration, and the static UI under `wwwroot/`.
- `backend/tests/InvoiceApp.Tests`: xUnit tests. Use one test class per class under test, named `<ClassUnderTest>Tests`. Use `FakeInvoiceRepository` for domain-service tests.
- `e2e`: Playwright tests in `tests/` and page objects in `pages/`.
- `docs/use-cases`: short briefs for possible features.
- `openspec`: OpenSpec configuration and change artifacts. Do not create or alter OpenSpec artifacts unless the task explicitly calls for the relevant OpenSpec workflow.

Design boundaries:

- Domain owns business rules and explicit business validation.
- API owns HTTP concerns, authentication, and translating domain failures into meaningful responses.
- Persistence implements Domain repository abstractions; do not leak persistence mechanics into Domain or UI.
- UI communicates only through API endpoints; it must not access persistence directly.
- Tests validate observable business behavior, including failure behavior and unchanged state.

Controllers live in `Controllers/`, one per resource, with route `api/[controller]`. Request bodies are `record` types declared inside their controller. Controllers inherit `ApiControllerBase` and use `Handle(...)` so expected service failures map consistently to 404, 409, and 400 responses. Register services in `Program.cs`; do not put business logic there.

All API endpoints require sign-in except `POST /api/auth/login`. Use `[RequireRole("...")]` for role-restricted operations. Existing demo accounts and roles are local-only fixtures, not production credentials; change them only when an approved feature increment requires it.

## Approved invoice-approval policy

These are binding business rules for the role-based approval feature.

### 1. Independent approval limits

1. For an invoice amount up to and including 50,000, either a Manager or a Director can independently approve it.
2. For an invoice amount above 50,000 and up to and including 500,000, only a Director can independently approve it.

### 2. Two-person approval

3. An invoice above 500,000 requires two approvals.
4. The first approver may be either a Manager or a Director.
5. The second approver must be a Director and must be a different user from the first approver.

### 3. Approval invariants

6. The same user must never count as two approvers, regardless of role or request.
7. After the first valid approval of an invoice above 500,000, its status remains `PendingApproval`.
8. The invoice becomes `Approved` only after the valid second approval.
9. Every rejected approval attempt must return a clear business reason.
10. A rejected attempt must not change invoice data, status, approval history, or timestamps.
11. Validate all policy conditions before mutating invoice state.
12. Approval recording must be atomic to prevent concurrent requests from bypassing approval requirements.

## Coding and design expectations

- Apply SOLID and clear separation of concerns.
- Prefer small, focused methods and clear names; do not use one-letter variables or `flag` parameters.
- Keep business rules in Domain services, never in controllers, `Program.cs`, or browser JavaScript.
- Preserve existing repository conventions: the interface lives in Domain and the in-memory implementation lives in API.
- Do not introduce direct persistence access from the UI.
- Every new rule or endpoint requires appropriate tests. Cover both accepted and rejected behavior.
- E2E tests use page objects and role-based locators (`getByRole`, `getByLabel`), never CSS or XPath selectors.
- Never commit real credentials, tokens, or customer data.

## Commands and prerequisites

The commands in this section are documented invocation commands, not evidence that they have run. At handoff, report the commands actually executed and their actual results.

Prerequisites:

- .NET 8 SDK for the backend and unit-test commands.
- Node.js and npm for E2E tests.
- Playwright packages and Chromium installed before running E2E tests.

Run the application:

```powershell
dotnet run --project backend/src/InvoiceApp.Api
```

Then open `http://localhost:5000`.

Build the .NET solution (the CI command):

```powershell
dotnet build backend/InvoiceApp.sln --configuration Release
```

Run unit tests after that build (the CI command):

```powershell
dotnet test backend/InvoiceApp.sln --configuration Release --no-build
```

For a standalone unit-test invocation:

```powershell
dotnet test backend/InvoiceApp.sln
```

Install E2E prerequisites and run Playwright:

```powershell
cd e2e
npm install
npx playwright install chromium
npm test
```

Playwright starts the API using `dotnet run --project ../backend/src/InvoiceApp.Api` and targets `http://localhost:5000`.

## Review expectations

For every approval-policy change, review and test:

- both inclusive boundaries: 50,000 and 500,000;
- values immediately above each boundary;
- duplicate approver identity, including role/request variations;
- Director-only second approval and distinct-user enforcement;
- `PendingApproval` after the first valid approval above 500,000;
- immutable invoice data, status, approval history, and timestamps after every rejected attempt;
- concurrency and atomicity at the persistence boundary;
- meaningful business error messages through the API and UI;
- every AI-generated test for assertion quality, realistic setup, and policy coverage.

Never accept tests merely because they pass. Tests must demonstrate the intended observable rule and guard against the relevant regression. Never silently modify unrelated code.

## Agent working rules

- Read the relevant source, tests, and existing OpenSpec context before editing.
- Follow the established architecture and make the smallest coherent change for the requested feature increment. Do not implement multiple feature increments in one task.
- Use OpenSpec only when explicitly asked for an OpenSpec workflow; do not fabricate specifications or generated artifacts.
- Do not commit, stage, push, install dependencies, or modify unrelated files unless explicitly instructed.
- At handoff, report files modified, commands/tests executed and their actual results, plus any tests not run and why.
- Do not fabricate test evidence, tool output, or verification claims.
