import type { Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class CheckoutInfoPage extends BasePage {
  private readonly firstNameInput = this.page.locator('[data-test="firstName"]');
  private readonly lastNameInput = this.page.locator('[data-test="lastName"]');
  private readonly postalCodeInput = this.page.locator('[data-test="postalCode"]');
  private readonly continueButton = this.page.locator('[data-test="continue"]');
  private readonly errorMessage = this.page.locator('[data-test="error"]');

  constructor(page: Page) {
    super(page);
  }

  async fillInfo(firstName: string, lastName: string, postalCode: string): Promise<CheckoutOverviewPage> {
    await this.fill(this.firstNameInput, firstName);
    await this.fill(this.lastNameInput, lastName);
    await this.fill(this.postalCodeInput, postalCode);
    await this.click(this.continueButton);
    return new CheckoutOverviewPage(this.page);
  }

  async getErrorText() {
    return this.errorMessage.innerText();
  }
}

export class CheckoutOverviewPage extends BasePage {
  private readonly finishButton = this.page.locator('[data-test="finish"]');
  private readonly summarySubtotal = this.page.locator('.summary_subtotal_label');
  private readonly summaryTotal = this.page.locator('.summary_total_label');

  constructor(page: Page) {
    super(page);
  }

  async getSubtotal() {
    const text = await this.summarySubtotal.innerText();
    return parseFloat(text.replace('Item total: $', ''));
  }

  async getTotal() {
    const text = await this.summaryTotal.innerText();
    return parseFloat(text.replace('Total: $', ''));
  }

  async finish(): Promise<CheckoutCompletePage> {
    await this.click(this.finishButton);
    return new CheckoutCompletePage(this.page);
  }
}

export class CheckoutCompletePage extends BasePage {
  private readonly completeHeader = this.page.locator('.complete-header');

  constructor(page: Page) {
    super(page);
  }

  async getConfirmationText() {
    return this.completeHeader.innerText();
  }
}
