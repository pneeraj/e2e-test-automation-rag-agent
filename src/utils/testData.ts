import type { Booking } from '@api/BookingClient';

/**
 * Simple builder instead of a fixed constant, so tests that create multiple
 * bookings in the same run don't collide and can still override just the
 * field they care about.
 */
export function buildBooking(overrides: Partial<Booking> = {}): Booking {
  const runId = Date.now();
  return {
    firstname: `Jordan${runId}`,
    lastname: 'Rivers',
    totalprice: 250,
    depositpaid: true,
    bookingdates: {
      checkin: '2026-01-10',
      checkout: '2026-01-15',
    },
    additionalneeds: 'Breakfast',
    ...overrides,
  };
}

export const saucedemoUsers = {
  standard: { username: 'standard_user', password: 'secret_sauce' },
  lockedOut: { username: 'locked_out_user', password: 'secret_sauce' },
  problem: { username: 'problem_user', password: 'secret_sauce' },
};
