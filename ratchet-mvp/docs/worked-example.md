# Worked example: the coherence ratchet, start to finish

This walks the packaged CLI across two real substrates:

1. the **staged billing slice** (`playground/_states/`), where a change is applied five ways and the
   signals move as the code decays and is then consolidated — every number below is reproducible;
2. a **public repo** (Flask), to show the architecture and change-history signals on code nobody
   wrote for this project.

Every command is copy-pasteable from `ratchet-mvp/`. Install first:

```sh
pip install -e .
coherence-ratchet --help        # measure | init | check
```

## 1. The staged billing slice

`playground/_states/` holds one subsystem in five states: a clean baseline, three rounds of
AI-assisted change that each copy-and-diverge an existing behaviour, and a consolidated end state.

```sh
for s in 00-baseline 01-orders 02-exports 03-loyalty 04-consolidated; do
  echo "== $s =="
  coherence-ratchet measure playground/_states/$s/billing --json
done
```

The signals move like this:

| state           | duplication ratio | redundant clusters | connascence (shared literals) | coupling density |
|-----------------|------------------:|-------------------:|------------------------------:|-----------------:|
| 00-baseline     | 0.00              | 0                  | 0                             | 0.40             |
| 01-orders       | 0.40              | 1                  | 0                             | 0.33             |
| 02-exports      | 0.71              | 2                  | 0                             | 0.29             |
| 03-loyalty      | 0.75              | 2                  | 1                             | 0.25             |
| 04-consolidated | 0.00              | 0                  | 1                             | 0.75             |

Two things in that table are the whole argument for a portfolio.

**Coupling falls as the code decays.** From baseline to the decayed peak, coupling density drops from
0.40 to 0.25. Each copied-and-diverged variant is a new, loosely-connected module, so average coupling
goes *down* while the system gets *worse*. A gate that watched coupling alone would read the decay as an
improvement. Duplication and connascence are the signals that actually rise with the damage.

**Consolidation raises coupling.** From the decayed peak to the consolidated state, duplication drops
to zero — the copies collapse into one shared helper — but coupling jumps from 0.25 to 0.75, because
every caller now depends on that helper. This is healthy coupling. It is exactly the move the ratchet
exists to reward, so coupling must be reported as a diagnostic and never ratcheted. Ratcheting it would
punish the fix.

That is why `WATCHED` is a portfolio — duplication, dependency cycles, connascence — and why coupling,
fan-in, hyperliminal pairs, and contagion are printed as diagnostics beside it, not enforced.

### Set a budget and run it as a gate

Take the baseline as the floor:

```sh
coherence-ratchet init playground/_states/00-baseline/billing --budgets coherence/budgets.json
```

Run the gate against the decayed state. It trips, and it trips on more than one signal:

```sh
coherence-ratchet check playground/_states/03-loyalty/billing --budgets coherence/budgets.json
```

```
RATCHET TRIPPED — coherence worsened past budget:
  ✗ connascence_shared: 1 > ceiling 0 (+1)
  ✗ duplication_ratio: 0.75 > ceiling 0.0 (+0.75)
  ✗ redundant_clusters: 2 > ceiling 0 (+2)
  ✗ redundant_functions: 6 > ceiling 0 (+6)
```

Exit code 1 — the same contract as a coverage ratchet failing CI. The team has two honest moves: reuse
the existing pattern instead of copying it, or accept the debt on the record.

### Accept the debt on the record

Sometimes the copy is the right call this week. Accepting it is a deliberate, owned, dated act, not a
silent pass:

```sh
coherence-ratchet check playground/_states/03-loyalty/billing \
  --budgets coherence/budgets.json \
  --accept --owner billing-team \
  --trigger "next settlement refactor / 2026-Q4" \
  --region billing.loyalty \
  --ledger coherence/coherence-ledger.jsonl
```

That writes one JSON line to the coherence-debt ledger:

```json
{"when": "2026-07-01", "region": "billing.loyalty", "owner": "billing-team",
 "repayment_trigger": "next settlement refactor / 2026-Q4",
 "breaches": [{"metric": "duplication_ratio", "ceiling": 0.0, "observed": 0.75}, ...]}
```

Debt priced, owned, and dated — the point of the whole exercise. Exit code 0, because accepting is a
decision, not a failure.

### Consolidation repays duplication — and the portfolio finds the residual

```sh
coherence-ratchet check playground/_states/04-consolidated/billing --budgets coherence/budgets.json
```

Duplication drops back to zero (the copies fold into `retry.retry`) and coupling rises to 0.75, which
the ratchet ignores because coupling is diagnostic. But the check still trips on one signal —
`connascence_shared` — because the consolidation left the retry count `3` hard-coded in two modules
that now agree by coincidence. This is the portfolio catching what a duplication-only gate would miss:
the obvious debt is repaid and the ratchet points straight at the next, subtler one. Fold the default
into one place, or accept it in the ledger with an owner and a date.

## 2. A public repo: Flask

The same command on code written by other people, with `--repo` to add the change-history signals
(hyperliminal coupling and contagion) from git:

```sh
git clone https://github.com/pallets/flask
coherence-ratchet measure flask/src/flask --repo flask
```

Measured on the current clone (24 modules):

```
architecture
  cycle ratio .......... 0.8333  (ratcheted)
  coupling density ..... 4.1667  (diagnostic)
  max fan-in ratio ..... 0.4583  (diagnostic)
connascence
  shared literals ...... 70      (ratcheted)
change history
  hyperliminal pairs ... 4       (diagnostic)
  contagion (mean) ..... 1.56    (diagnostic)
```

The cycle ratio (0.83) is the headline architectural signal: most of Flask's internal modules sit in a
dependency cycle. The four hyperliminal pairs are modules that co-change in git history but share no
static import edge — hidden coupling the dependency graph cannot see. On a working repo, the value is
not a verdict on Flask; it is that these signals are computed from the code and its history with no
manual mapping, so they cannot go stale the way a hand-drawn diagram does.

## What this is, and is not

This is an MVP, and the docs say so plainly:

- Python only, via the standard-library AST. No other language.
- Duplication detection is O(n²) over function fingerprints — fine for a subsystem, not tuned for a
  monorepo.
- Duplication is a **proxy**. It catches copy-and-diverge, which is the common AI-assisted failure, but
  it is not a semantic judge. The method puts an LLM semantic pass and a behaviour-complete proof
  *above* this deterministic floor; they are not in this tool.
- The hyperliminal and contagion signals need real git history to mean anything.

The deterministic layer is a floor a team can run today. It is not the whole method, and it does not
promise that consolidation always pays. It makes the decay visible, prices it in an owned ledger, and
shows where acting is worth it.
