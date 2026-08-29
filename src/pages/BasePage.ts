import type { Locator, Page } from '@playwright/test';

/**
 * Small set of helpers every page object ends up needing. Kept intentionally
 * thin - this is not meant to be a generic UI-automation library, just the
 * handful of things that show up in more than one page.
 */
export class BasePage {
  constructor(protected readonly page: Page) {}

  async goto(path = '/') {
    await this.page.goto(path);
  }

  protected async click(locator: Locator) {
    await locator.waitFor({ state: 'visible' });
    await locator.click();
  }

  protected async fill(locator: Locator, value: string) {
    await locator.waitFor({ state: 'visible' });
    await locator.fill(value);
  }
}
