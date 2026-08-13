import type { components } from "./generated/schema.js";

export type PriceResponse = components["schemas"]["PriceResponse"];

export function renderReceipt(response: PriceResponse, expectedTotalCents: number): string {
  if (response.total_cents !== expectedTotalCents) {
    throw new Error(
      `pricing semantics changed: expected ${expectedTotalCents}, received ${response.total_cents}`,
    );
  }
  return `${response.order_id}: ${response.currency} ${(response.total_cents / 100).toFixed(2)}`;
}

