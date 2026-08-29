import { test as base } from '@playwright/test';
import { BookingClient } from '@api/BookingClient';

type ApiFixtures = {
  bookingClient: BookingClient;
};

export const test = base.extend<ApiFixtures>({
  bookingClient: async ({ request }, use) => {
    await use(new BookingClient(request));
  },
});

export { expect } from '@playwright/test';
