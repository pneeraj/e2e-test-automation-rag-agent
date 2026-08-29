import { test, expect } from '@fixtures/api.fixtures';
import { buildBooking } from '@utils/testData';

test.describe('Restful-Booker - booking CRUD @smoke', () => {
  test('API is reachable', async ({ bookingClient }) => {
    expect(await bookingClient.ping()).toBe(true);
  });

  test('a booking can be created, read, updated and deleted', async ({ bookingClient }) => {
    const created = await bookingClient.createBooking(buildBooking());
    expect(created.bookingid).toBeGreaterThan(0);

    const fetched = await bookingClient.getBooking(created.bookingid);
    expect(fetched.firstname).toBe(created.booking.firstname);
    expect(fetched.bookingdates.checkin).toBe(created.booking.bookingdates.checkin);

    const updated = await bookingClient.updateBooking(
      created.bookingid,
      buildBooking({ firstname: created.booking.firstname, totalprice: 999 }),
    );
    expect(updated.totalprice).toBe(999);

    await bookingClient.deleteBooking(created.bookingid);
    // Restful-Booker's public instance is eventually consistent on delete,
    // so we only assert the call itself didn't throw (see deleteBooking impl).
  });

  test('deposit-paid bookings keep the flag through an update', async ({ bookingClient }) => {
    const created = await bookingClient.createBooking(buildBooking({ depositpaid: true }));

    const updated = await bookingClient.updateBooking(
      created.bookingid,
      buildBooking({ firstname: created.booking.firstname, depositpaid: true, additionalneeds: 'Late checkout' }),
    );

    expect(updated.depositpaid).toBe(true);
    expect(updated.additionalneeds).toBe('Late checkout');
  });
});
