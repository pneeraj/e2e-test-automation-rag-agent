# Flaky selectors

Symptoms: intermittent "element not found" or "element is not attached to the
DOM" errors, usually only under parallel workers or on CI, never locally.

Common root causes we've seen:
- Locator built from visible text that changes with A/B tests or currency
  locale (e.g. "$29.99" vs "29,99 EUR").
- Clicking an element right after a client-side route change, before the new
  DOM has settled - the old node gets detached mid-click.
- Using nth-child/nth-of-type instead of data-test attributes, so a layout
  change silently reorders which element the index resolves to.

Fix pattern: prefer a stable data-test/data-testid attribute (see how
InventoryPage.addToCartButton builds its locator). If the app doesn't expose
one yet, that's a bug to raise with the dev team, not something to patch
around with a longer wait.
