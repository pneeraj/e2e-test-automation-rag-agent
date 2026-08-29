import * as dotenv from 'dotenv';

dotenv.config();

/**
 * Every test/page-object/api-client reads config from here instead of
 * touching process.env directly, so there is exactly one place that knows
 * about defaults and env var names.
 */
export const env = {
  sauce: {
    baseUrl: process.env.SAUCE_BASE_URL ?? 'https://www.saucedemo.com',
    username: process.env.SAUCE_USERNAME ?? 'standard_user',
    password: process.env.SAUCE_PASSWORD ?? 'secret_sauce',
  },
  bookingApi: {
    baseUrl: process.env.BOOKING_API_BASE_URL ?? 'https://restful-booker.herokuapp.com',
    username: process.env.BOOKING_API_USERNAME ?? 'admin',
    password: process.env.BOOKING_API_PASSWORD ?? 'password123',
  },
  isCI: !!process.env.CI,
};
