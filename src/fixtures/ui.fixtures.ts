import { test as base } from '@playwright/test';
import { LoginPage } from '@pages/LoginPage';
import { InventoryPage } from '@pages/InventoryPage';

type UiFixtures = {
  loginPage: LoginPage;
  loggedInInventoryPage: InventoryPage;
};

/**
 * `loggedInInventoryPage` saves every checkout/cart test from repeating the
 * same three login steps - it logs in once via the standard user and hands
 * back the inventory page already loaded.
 */
export const test = base.extend<UiFixtures>({
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.open();
    await use(loginPage);
  },

  loggedInInventoryPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await loginPage.open();
    const inventoryPage = await loginPage.login(
      process.env.SAUCE_USERNAME ?? 'standard_user',
      process.env.SAUCE_PASSWORD ?? 'secret_sauce',
    );
    await use(inventoryPage);
  },
});

export { expect } from '@playwright/test';
