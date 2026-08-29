import type { Page } from '@playwright/test';
import { BasePage } from './BasePage';
import { CheckoutInfoPage } from './CheckoutPage';

export class CartPage extends BasePage {
  private readonly cartItems = this.page.locator('.cart_item');
  private readonly checkoutButton = this.page.locator('[data-test="checkout"]');
  private readonly continueShoppingButton = this.page.locator('[data-test="continue-shopping"]');

  constructor(page: Page) {
    super(page);
  }

  async getItemNames() {
    return this.cartItems.locator('.inventory_item_name').allTextContents();
  }

  async getItemCount() {
    return this.cartItems.count();
  }

  async removeItem(productName: string) {
    const slug = productName.toLowerCase().replace(/\s+/g, '-');
    await this.click(this.page.locator(`[data-test="remove-${slug}"]`));
  }

  async continueShopping() {
    await this.click(this.continueShoppingButton);
  }

  async proceedToCheckout(): Promise<CheckoutInfoPage> {
    await this.click(this.checkoutButton);
    return new CheckoutInfoPage(this.page);
  }
}
