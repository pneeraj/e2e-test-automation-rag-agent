# Timeout / slow response failures

Symptoms: "Timeout 30000ms exceeded" on navigation or action steps.

Common root causes:
- Third-party demo services (SauceDemo, Restful-Booker, etc.) we don't
  control occasionally rate-limit or cold-start slowly - this shows up as a
  spike in timeouts across unrelated tests at the same time, not a single
  broken spec.
- A previous test left the browser context in a modal/dialog state that
  blocks the next action from ever becoming actionable.
- CI runners under memory pressure (too many parallel workers for the
  available cores) slow every action down uniformly rather than failing one
  specific test.

Fix pattern: check whether failures are clustered in time across multiple,
unrelated specs before assuming the test logic itself is wrong.
