include "DiscountRounding.dfy"

function HalfEven(milliCents: int): int
  requires milliCents >= 0
{
  var whole := milliCents / 10;
  var remainder := milliCents % 10;
  if remainder > 5 || (remainder == 5 && whole % 2 == 1) then whole + 1 else whole
}

function MutatedPriceCents(subtotalMilli: int, discountBps: int): int
  requires subtotalMilli >= 0
  requires 0 <= discountBps <= 10000
{
  HalfEven(DiscountedMilli(subtotalMilli, discountBps))
}

// This claimed equivalence is false. Dafny must reject it at the half-cent boundary.
lemma IncorrectEquivalence(subtotalMilli: int, discountBps: int)
  requires subtotalMilli >= 0
  requires 0 <= discountBps <= 10000
  ensures PriceCents(subtotalMilli, discountBps) == MutatedPriceCents(subtotalMilli, discountBps)
{
}

