import { test, expect } from '@fixtures/ui.fixtures';
import { saucedemoUsers } from '@utils/testData';

test.describe('SauceDemo login @smoke', () => {
  test('standard user can log in and land on the inventory page', async ({ loginPage, page }) => {
    await loginPage.login(saucedemoUsers.standard.username, saucedemoUsers.standard.password);

    await expect(page).toHaveURL(/inventory/);
    await expect(page.locator('.inventory_list')).toBeVisible();
  });

  test('locked out user sees an explicit error', async ({ loginPage }) => {
    await loginPage.login(saucedemoUsers.lockedOut.username, saucedemoUsers.lockedOut.password);

    await expect.poll(() => loginPage.getErrorText()).toContain('locked out');
  });

  test('empty credentials are rejected client-side', async ({ loginPage }) => {
    await loginPage.login('', '');

    await expect.poll(() => loginPage.getErrorText()).toContain('Username is required');
  });
});
