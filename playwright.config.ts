import { defineConfig, devices } from '@playwright/test';
import { env } from './src/utils/env';

/**
 * Three independent suites share one Playwright installation:
 *  - ui        -> desktop browser, Page Object Model, runs against SauceDemo
 *  - api       -> no browser at all, uses request context against Restful-Booker
 *  - mobile    -> same UI specs' journeys, re-run under real device emulation
 *
 * Splitting them by testDir (instead of tags) keeps `npx playwright test`
 * scoped and predictable, and lets CI run the three in parallel jobs.
 */
export default defineConfig({
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  forbidOnly: env.isCI,
  retries: env.isCI ? 1 : 0,
  workers: env.isCI ? 2 : undefined,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
  use: {
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
  },
  projects: [
    {
      name: 'ui-chrome',
      testDir: './tests/ui',
      use: { ...devices['Desktop Chrome'], baseURL: env.sauce.baseUrl },
    },
    {
      name: 'api',
      testDir: './tests/api',
      use: { baseURL: env.bookingApi.baseUrl },
    },
    {
      name: 'mobile-chrome',
      testDir: './tests/mobile',
      use: { ...devices['Pixel 7'], baseURL: env.sauce.baseUrl },
    },
    {
      name: 'mobile-safari',
      testDir: './tests/mobile',
      use: { ...devices['iPhone 14'], baseURL: env.sauce.baseUrl },
    },
  ],
});
