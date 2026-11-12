# Invoice Approval Demo App

A small invoice approval app used for live AI-in-SDLC demos. It is deliberately simple: a .NET 8 API, a plain web UI, and an in-memory store, so it runs with one command and no database.

## Run it

```
dotnet run --project backend/src/InvoiceApp.Api
```

Open http://localhost:5000 and sign in:

| User | Password | Role |
| --- | --- | --- |
| `demo.manager` | `ChangeMe123!` | Manager |
| `demo.director` | `ChangeMe123!` | Director |
| `demo.director2` | `ChangeMe123!` | Director |
| `demo.admin` | `ChangeMe123!` | Admin |

These are demo accounts for a local, in-memory app. They are not real credentials.

## What it does

1. Create an invoice (it starts as a draft).
2. Submit it for approval.
3. An authorized approver approves it or rejects it with a reason.

Invoices move through Draft, Pending Approval, then Approved or Rejected. Approval limits are role-based:

- A Manager or Director can independently approve invoices up to and including 50,000.
- Only a Director can independently approve invoices above 50,000 and up to and including 500,000.
- Invoices above 500,000 need two approvals. The first approver can be a Manager or Director; the second must be a different Director.
- The API derives approver identity and role from the signed-in account. Rejected approval attempts return a reason and leave the invoice unchanged.

Approval history is shown with each invoice so users can see approval progress.

## Tests

Run the backend unit and API tests from the repository root:

```
dotnet test backend/InvoiceApp.sln
```

Run the browser tests from `e2e` (Node.js dependencies and Playwright Chromium must be installed):

```powershell
cd e2e
npm install
npx playwright install chromium
npm test
```

To watch the browser while the tests run:

```powershell
npm run test:headed
```

To run only the role-based approval scenarios:

```powershell
npx playwright test tests\role-based-invoice-approval.spec.ts
```

## Project layout

```
backend/
  src/InvoiceApp.Domain   business rules
  src/InvoiceApp.Api      controllers, sign-in, web UI (wwwroot)
  tests/InvoiceApp.Tests  xUnit tests
docs/use-cases            short feature briefs
AGENTS.md                 conventions for AI coding agents
```

## Use cases

- [UC-1 Bulk invoice approval](docs/use-cases/UC-1-bulk-approval.md)
- [UC-2 Partial approval](docs/use-cases/UC-2-partial-approval.md)

### Mutation tests

Install the .NET 8-compatible Stryker.NET version:

```powershell
dotnet tool install -g dotnet-stryker --version 4.13.0
cd backend\tests\InvoiceApp.Tests
dotnet stryker --project InvoiceApp.Domain.csproj --configuration Release