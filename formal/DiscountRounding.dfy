// A deliberately small verified kernel. Amounts are milli-cents; rates are basis points.

function HalfUp(milliCents: int): int
  requires milliCents >= 0
{
  (milliCents + 5) / 10
}

function DiscountedMilli(subtotalMilli: int, discountBps: int): int
  requires subtotalMilli >= 0
  requires 0 <= discountBps <= 10000
{
  subtotalMilli * (10000 - discountBps) / 10000
}

function PriceCents(subtotalMilli: int, discountBps: int): int
  requires subtotalMilli >= 0
  requires 0 <= discountBps <= 10000
{
  HalfUp(DiscountedMilli(subtotalMilli, discountBps))
}

function ConsolidatedPriceCents(subtotalMilli: int, discountBps: int): int
  requires subtotalMilli >= 0
  requires 0 <= discountBps <= 10000
{
  var discounted := subtotalMilli * (10000 - discountBps) / 10000;
  var whole := discounted / 10;
  var remainder := discounted % 10;
  if remainder >= 5 then whole + 1 else whole
}

lemma FaithfulConsolidation(subtotalMilli: int, discountBps: int)
  requires subtotalMilli >= 0
  requires 0 <= discountBps <= 10000
  ensures PriceCents(subtotalMilli, discountBps) == ConsolidatedPriceCents(subtotalMilli, discountBps)
{
}
