import { expect, test } from '@playwright/test';
import { InvoiceAppPage } from '../pages/invoice-app.page';

test('Manager can approve ₹50,000 and receives a rejection above the limit', async ({ page }) => {
  const app = new InvoiceAppPage(page);
  await app.signIn('demo.manager');
  const allowedId = await app.createAndSubmitInvoice('50000');
  const overLimitId = await app.createAndSubmitInvoice('50000.01');
  await app.openApprovals();
  await app.approvalButton(allowedId).click();
  await app.expectInvoiceProgress(allowedId, '1/1 approval: demo.manager (Manager)');
  await app.openApprovals();
  await app.approvalButton(overLimitId).click();
  await app.expectDecisionError('Invoices above 50,000 require Director approval.');
  await app.expectInvoiceState(overLimitId, 'Pending Approval', '0/1 approval');
});
