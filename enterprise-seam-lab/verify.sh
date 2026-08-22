#!/bin/sh
set -eu

: "${OASDIFF:?Set OASDIFF to the pinned oasdiff 1.27.0 executable}"
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

# The manifest pins the oracle as well as the inputs, so it is checked before anything runs. Without
# this the assertion blocks below could be edited away and the lab would still print "passed" with
# every recorded hash intact.
python3 "$HERE/../tools/manifest-check.py" "$HERE" check

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

# Compile evidence is generated per contract rather than only from the baseline. The book's claim for
# the optional-addition case is that the consumer still compiles once the field is added, and that is
# only tested if the types come from the changed contract: `npm run generate` is pinned to
# baseline.yaml, so running it alone left that claim unexecuted.
for contract in baseline optional-addition; do
  npx openapi-typescript "$HERE/contracts/$contract.yaml" -o src/generated/schema.d.ts
  npx tsc --noEmit
  echo "Expected result: the consumer compiles against $contract."
done

# The semantic-change contract differs from the baseline only in its version string and a description,
# so a compile against it is trivially clean. That is the point of the case, and the evidence that
# matters for it is the consumer run below rather than the compile.
npx openapi-typescript "$HERE/contracts/baseline.yaml" -o src/generated/schema.d.ts
npm run build

PYTHONPATH="$HERE/producer" python3 "$HERE/producer/emit.py" pricing > /tmp/stewardship-price-good.json
PYTHONPATH="$HERE/producer" python3 "$HERE/producer/emit.py" pricing_half_even > /tmp/stewardship-price-mutated.json

node dist/test-consumer.js /tmp/stewardship-price-good.json 1
if node dist/test-consumer.js /tmp/stewardship-price-mutated.json 1; then
  echo "ERROR: consumer evidence missed the rounding mutation" >&2
  exit 1
else
  echo "Expected result: consumer evidence refuted the rounding mutation."
fi

echo "Enterprise seam lab passed."
