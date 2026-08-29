import { test, expect } from '@fixtures/ui.fixtures';

/**
 * Same user journey as tests/ui, but this file only runs under the
 * mobile-chrome / mobile-safari projects (see playwright.config.ts), so it
 * exercises the responsive layout on real device viewports and touch input.
 */
test.describe('SauceDemo shopping on mobile viewports', () => {
  test('user can log in and add an item to the cart', async ({ loggedInInventoryPage }) => {
    await loggedInInventoryPage.addProductToCart('Sauce Labs Backpack');

    expect(await loggedInInventoryPage.getCartCount()).toBe(1);
  });

  test('cart page lists the item added on a small screen', async ({ loggedInInventoryPage }) => {
    await loggedInInventoryPage.addProductToCart('Sauce Labs Fleece Jacket');

    const cartPage = await loggedInInventoryPage.openCart();
    expect(await cartPage.getItemNames()).toContain('Sauce Labs Fleece Jacket');
  });
});
