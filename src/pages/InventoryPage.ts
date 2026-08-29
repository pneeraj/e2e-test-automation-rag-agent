import type { Page } from '@playwright/test';
import { BasePage } from './BasePage';
import { CartPage } from './CartPage';

export class InventoryPage extends BasePage {
  private readonly cartBadge = this.page.locator('.shopping_cart_badge');
  private readonly cartLink = this.page.locator('.shopping_cart_link');
  private readonly sortDropdown = this.page.locator('[data-test="product-sort-container"]');
  private readonly inventoryItemNames = this.page.locator('.inventory_item_name');
  private readonly inventoryItemPrices = this.page.locator('.inventory_item_price');

  constructor(page: Page) {
    super(page);
  }

  private addToCartButton(productName: string) {
    // SauceDemo builds the id from the product name, e.g. "add-to-cart-sauce-labs-backpack"
    const slug = productName.toLowerCase().replace(/\s+/g, '-');
    return this.page.locator(`[data-test="add-to-cart-${slug}"]`);
  }

  async addProductToCart(productName: string) {
    await this.click(this.addToCartButton(productName));
  }

  async sortBy(option: 'az' | 'za' | 'lohi' | 'hilo') {
    await this.sortDropdown.selectOption(option);
  }

  async getProductNames() {
    return this.inventoryItemNames.allTextContents();
  }

  async getProductPrices() {
    const raw = await this.inventoryItemPrices.allTextContents();
    return raw.map((price) => parseFloat(price.replace('$', '')));
  }

  async getCartCount() {
    return (await this.cartBadge.isVisible()) ? Number(await this.cartBadge.innerText()) : 0;
  }

  async openCart(): Promise<CartPage> {
    await this.click(this.cartLink);
    return new CartPage(this.page);
  }
}
