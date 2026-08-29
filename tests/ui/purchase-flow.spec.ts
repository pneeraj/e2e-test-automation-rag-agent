import { test, expect } from '@fixtures/ui.fixtures';

test.describe('SauceDemo checkout flow', () => {
  test('customer can buy two items end to end @smoke', async ({ loggedInInventoryPage }) => {
    await loggedInInventoryPage.addProductToCart('Sauce Labs Backpack');
    await loggedInInventoryPage.addProductToCart('Sauce Labs Bike Light');
    expect(await loggedInInventoryPage.getCartCount()).toBe(2);

    const cartPage = await loggedInInventoryPage.openCart();
    expect(await cartPage.getItemNames()).toEqual(['Sauce Labs Backpack', 'Sauce Labs Bike Light']);

    const checkoutInfoPage = await cartPage.proceedToCheckout();
    const overviewPage = await checkoutInfoPage.fillInfo('Jordan', 'Rivers', '94107');

    // sanity-check the math instead of hardcoding a total that breaks the moment prices change
    const subtotal = await overviewPage.getSubtotal();
    const total = await overviewPage.getTotal();
    expect(total).toBeGreaterThan(subtotal);

    const completePage = await overviewPage.finish();
    await expect.poll(() => completePage.getConfirmationText()).toContain('Thank you for your order');
  });

  test('checkout is blocked when postal code is missing', async ({ loggedInInventoryPage }) => {
    await loggedInInventoryPage.addProductToCart('Sauce Labs Backpack');
    const cartPage = await loggedInInventoryPage.openCart();
    const checkoutInfoPage = await cartPage.proceedToCheckout();

    await checkoutInfoPage.fillInfo('Jordan', 'Rivers', '');

    await expect.poll(() => checkoutInfoPage.getErrorText()).toContain('Postal Code is required');
  });

  test('products can be sorted by price low to high', async ({ loggedInInventoryPage }) => {
    await loggedInInventoryPage.sortBy('lohi');
    const prices = await loggedInInventoryPage.getProductPrices();
    const sorted = [...prices].sort((a, b) => a - b);
    expect(prices).toEqual(sorted);
  });
});
