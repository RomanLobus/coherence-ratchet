import { readFileSync } from "node:fs";
import { renderReceipt, type PriceResponse } from "./consumer.js";

const responsePath = process.argv[2];
const expectedText = process.argv[3];
if (responsePath === undefined || expectedText === undefined) {
  throw new Error("usage: test-consumer RESPONSE_JSON EXPECTED_TOTAL_CENTS");
}
const response = JSON.parse(readFileSync(responsePath, "utf8")) as PriceResponse;
const expected = Number(expectedText);
console.log(renderReceipt(response, expected));
