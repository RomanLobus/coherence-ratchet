# Enterprise seam lab

The checkout-pricing case crosses a team and language boundary here. A Python pricing producer owns
the calculation. A TypeScript receipt consumer owns presentation and a consumer-side semantic check.
OpenAPI 3.1 is their shared contract.

The lab demonstrates three different results:

- Adding optional `discount_tier` is schema-compatible.
- Replacing required `total_cents` with `total` is a breaking contract change.
- Changing half-up rounding to half-even leaves the schema unchanged, so the schema check passes;
  the consumer evidence still refutes the change at the half-cent boundary.

This division is deliberate. OpenAPI compatibility, generated types, bounded behaviour comparison,
and human review answer different questions. Passing one never inherits the claim made by another.

## Run

```sh
OASDIFF=/path/to/oasdiff ./verify.sh
```

The verified run uses oasdiff 1.27.0, openapi-typescript 7.13.0, and TypeScript 5.9.3. The producer
and consumer remain in one lab directory for reproducibility, but each has its own package boundary
and can be moved into a separate repository without changing the contract.

