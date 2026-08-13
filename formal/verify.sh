#!/bin/sh
set -eu

: "${DAFNY:?Set DAFNY to the Dafny 4.11.0 executable}"
: "${TLA2TOOLS:?Set TLA2TOOLS to the TLA+ tools 1.7.1 jar}"

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

"$DAFNY" verify "$HERE/DiscountRounding.dfy"

if "$DAFNY" verify "$HERE/DiscountRoundingMutation.dfy"; then
  echo "ERROR: the known half-even mutation unexpectedly verified" >&2
  exit 1
else
  echo "Expected result: Dafny rejected the half-even equivalence claim."
fi

java -XX:+UseSerialGC -cp "$TLA2TOOLS" tlc2.TLC -cleanup -config "$HERE/Safe.cfg" "$HERE/ContractRollout.tla"

if java -XX:+UseSerialGC -cp "$TLA2TOOLS" tlc2.TLC -cleanup -config "$HERE/Unsafe.cfg" "$HERE/ContractRollout.tla"; then
  echo "ERROR: the unsafe rollout unexpectedly satisfied the safety invariant" >&2
  exit 1
else
  echo "Expected result: TLC found an unsupported-consumer counterexample."
fi

echo "Formal-methods lab passed."

