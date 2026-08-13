#!/bin/sh
set -eu

: "${OASDIFF:?Set OASDIFF to the pinned oasdiff 1.27.0 executable}"
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

"$OASDIFF" breaking --fail-on ERR "$HERE/contracts/baseline.yaml" "$HERE/contracts/optional-addition.yaml"

if "$OASDIFF" breaking --fail-on ERR "$HERE/contracts/baseline.yaml" "$HERE/contracts/breaking-rename.yaml"; then
  echo "ERROR: the required-field rename was not reported as breaking" >&2
  exit 1
else
  echo "Expected result: OpenAPI check rejected the total_cents rename."
fi

"$OASDIFF" breaking --fail-on ERR "$HERE/contracts/baseline.yaml" "$HERE/contracts/semantic-change.yaml"
echo "Expected result: the schema check cannot see the rounding change."

cd "$HERE/consumer"
npm ci
npm run check
npm run build

PYTHONPATH="$HERE/producer" python3 "$HERE/producer/emit.py" pricing > /tmp/seam-lab-price-good.json
PYTHONPATH="$HERE/producer" python3 "$HERE/producer/emit.py" pricing_half_even > /tmp/seam-lab-price-mutated.json

node dist/test-consumer.js /tmp/seam-lab-price-good.json 1
if node dist/test-consumer.js /tmp/seam-lab-price-mutated.json 1; then
  echo "ERROR: consumer evidence missed the rounding mutation" >&2
  exit 1
else
  echo "Expected result: consumer evidence refuted the rounding mutation."
fi

echo "Enterprise seam lab passed."
