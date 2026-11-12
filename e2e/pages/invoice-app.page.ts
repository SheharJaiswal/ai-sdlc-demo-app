import { expect, Page } from '@playwright/test';

export class InvoiceAppPage {
  constructor(private readonly page: Page) {}

  async signIn(username: string) {
    await this.page.goto('/');
    await this.page.getByLabel('Username').fill(username);
    await this.page.getByLabel('Password').fill('ChangeMe123!');
    await this.page.getByRole('button', { name: 'Sign in' }).click();
  }

  async createAndSubmitInvoice(amount: string): Promise<string> {
    const customer = `Approval test ${amount} ${Date.now()}`;
    await this.page.getByLabel('Customer name').fill(customer);
    await this.page.getByLabel('Amount').fill(amount);
    await this.page.getByRole('button', { name: 'Create invoice' }).click();
    const row = this.page.getByRole('row', { name: new RegExp(customer) });
    const id = await row.getByRole('cell').first().textContent();
    await row.getByRole('button', { name: /Submit invoice/ }).click();
    return id!;
  }

  async openApprovals() {
    await this.page.getByRole('tab', { name: 'Approvals' }).click();
  }

  approvalButton(invoiceId: string) {
    return this.page.getByRole('button', { name: `Approve invoice ${invoiceId}` });
  }

  async expectPendingProgress(invoiceId: string, text: string) {
    const invoice = this.page.getByRole('listitem').filter({ hasText: invoiceId });
    await expect(invoice).toBeVisible();
    await expect(invoice).toContainText(text);
  }

  async expectInvoiceProgress(invoiceId: string, text: string) {
    await this.expectInvoiceState(invoiceId, 'Approved', text);
  }

  async expectInvoiceState(invoiceId: string, status: string, progress: string) {
    await this.page.getByRole('tab', { name: 'Invoices' }).click();
    const invoice = this.page.getByRole('row').filter({
      has: this.page.getByRole('cell', { name: invoiceId, exact: true }),
    });
    await expect(invoice).toBeVisible();
    await expect(invoice.getByRole('cell').nth(3)).toHaveText(status);
    await expect(invoice.getByRole('cell').nth(4)).toHaveText(progress);
  }

  async expectDecisionError(text: string) {
    await expect(this.page.getByRole('alert').filter({ hasText: text })).toBeVisible();
  }
}
