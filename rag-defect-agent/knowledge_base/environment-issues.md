# Environment / configuration issues

Symptoms: a suite that passes locally fails only in CI, or only for one
person, with an error that looks unrelated to the actual test logic (401/403
on the first API call, wrong base URL, "invalid credentials").

Common root causes:
- Missing or stale .env value - most often BOOKING_API_BASE_URL or
  SAUCE_USERNAME/SAUCE_PASSWORD pointing at a decommissioned demo account.
- Jenkins credentials binding injecting a secret under a different env var
  name than the one src/utils/env.ts expects.
- Auth token cached across test runs (see BookingClient.getAuthToken) going
  stale after the public demo API restarts.

Fix pattern: reproduce with the exact same .env used in CI before touching
any test code.
