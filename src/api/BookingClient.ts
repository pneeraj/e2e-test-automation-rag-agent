import type { APIRequestContext } from '@playwright/test';

export interface BookingDates {
  checkin: string;
  checkout: string;
}

export interface Booking {
  firstname: string;
  lastname: string;
  totalprice: number;
  depositpaid: boolean;
  bookingdates: BookingDates;
  additionalneeds?: string;
}

export interface CreatedBooking {
  bookingid: number;
  booking: Booking;
}

/**
 * Wraps the handful of Restful-Booker endpoints the suite touches. Auth token
 * is fetched lazily and cached for the lifetime of the client, since every
 * write operation (PUT/DELETE) needs it but reads don't.
 */
export class BookingClient {
  private token: string | undefined;

  constructor(
    private readonly request: APIRequestContext,
    private readonly credentials = {
      username: process.env.BOOKING_API_USERNAME ?? 'admin',
      password: process.env.BOOKING_API_PASSWORD ?? 'password123',
    },
  ) {}

  private async getAuthToken(): Promise<string> {
    if (this.token) return this.token;

    const response = await this.request.post('/auth', { data: this.credentials });
    if (!response.ok()) {
      throw new Error(`Failed to authenticate against booking API: ${response.status()}`);
    }
    const body = await response.json();
    this.token = body.token;
    return this.token as string;
  }

  async createBooking(booking: Booking): Promise<CreatedBooking> {
    const response = await this.request.post('/booking', { data: booking });
    if (!response.ok()) {
      throw new Error(`createBooking failed with ${response.status()}`);
    }
    return response.json();
  }

  async getBooking(bookingId: number): Promise<Booking> {
    const response = await this.request.get(`/booking/${bookingId}`);
    if (!response.ok()) {
      throw new Error(`getBooking(${bookingId}) failed with ${response.status()}`);
    }
    return response.json();
  }

  async updateBooking(bookingId: number, booking: Booking): Promise<Booking> {
    const token = await this.getAuthToken();
    const response = await this.request.put(`/booking/${bookingId}`, {
      data: booking,
      headers: { Cookie: `token=${token}` },
    });
    if (!response.ok()) {
      throw new Error(`updateBooking(${bookingId}) failed with ${response.status()}`);
    }
    return response.json();
  }

  async deleteBooking(bookingId: number): Promise<void> {
    const token = await this.getAuthToken();
    const response = await this.request.delete(`/booking/${bookingId}`, {
      headers: { Cookie: `token=${token}` },
    });
    if (response.status() !== 201 && response.status() !== 200) {
      throw new Error(`deleteBooking(${bookingId}) failed with ${response.status()}`);
    }
  }

  async ping(): Promise<boolean> {
    const response = await this.request.get('/ping');
    return response.status() === 201;
  }
}
