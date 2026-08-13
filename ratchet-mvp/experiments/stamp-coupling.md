# Experiment — stamp coupling from the derived self-model

**Direction:** the `arch/anti/` antipatterns catalogue. Stamp coupling (Myers, *Composite/Structured
Design*; catalogued as an architecture antipattern) is passing a whole data structure to a consumer
that needs only part of it. The consumer is then coupled to the entire shape: a change to a field it
never touches can still force it to change, and the contract hides what is really depended on. The
observation this probe tests is that the derived self-model already records which keys of an entity
each site actually uses (`per_site_keys`), so that data is a latent stamp-coupling detector — no new
extraction, just a comparison. `probe_stamp_coupling.py` builds it: for each function parameter that
the codebase treats as an entity, compare the keys the function uses against the entity's full observed
shape, and flag under-use (especially when the whole thing is then forwarded onward).

## Result A — on a data-entity fixture, the detector is exact

The fixture has one entity (`order`, five keys, used in full by `order_summary`), two stamp-coupling
sites, and one clean control:

| site | uses | of full shape | reading |
|---|---|---|---|
| `audit.log_order(order)` | `id` | 5 keys | receives the whole order, uses one field → **flagged** |
| `audit.archive(order)` | (none) | 5 keys | forwards the whole order, uses nothing → **flagged (forwards whole)** |
| `clean.lookup_order(order_id)` | — | — | takes only the id it needs → **not flagged** (the good design) |

Both stamp-coupling sites are caught; the control that passes only the scalar it needs is not. The
detector correctly refuses to invent an entity for `order_id` (a plain string), so the clean design
reads as clean.

## Result B — on real code the naive reading is almost all false positives, and the fix is precise

Run unrestricted (any attribute or subscript access counts), the detector fires 22 times on requests
and 48 on flask. Nearly all are wrong. They are service **objects** — `request`, `app`, Click's `ctx`,
the response `r` — passed to a method that reads one attribute. That is normal object-oriented
collaboration, not stamp coupling; the object is a dependency, not a data structure being over-shared.
The union-of-all-attributes denominator makes any single-attribute use look like gross under-use.

The refinement that fixes it is the antipattern's own definition: stamp coupling is about **data
structures**, not collaborators. Restricting the detector to string-subscript access (`order["id"]`,
the way dict-shaped data is read) rather than attribute access (`request.headers`, the way objects are
used) changes the picture completely:

| repo | naive (incl. attributes) | data-contract only | true positives lost |
|---|---:|---:|---:|
| fixture | 2 | 2 | 0 |
| requests | 22 | **0** | 0 |
| flask | 48 | **0** | 0 |

Every false positive on the two libraries disappears, and the fixture's true positives survive. The
signal fires where a codebase passes dict-shaped data around and uses little of it, and stays silent
where it passes service objects — which is exactly the distinction the antipattern draws and the naive
metric could not.

## What this tells the book

Three things, and the third is the point.

1. **A named antipattern is deterministically detectable from data the self-model already holds.** The
   entity shapes derived in Move 1 are not only for "what is the canonical order" — the same per-site
   key record grounds a stamp-coupling signal. It maps straight onto the worked example: a report that
   receives the whole `order` to print an id is stamp-coupled to fields it never reads.

2. **The signal is a triage/ranking instrument, not a gate.** Even in data-contract mode it cannot know
   whether a forwarded structure is genuinely over-shared or handed to a callee that uses the rest;
   confirming that needs the call graph or the semantic layer. This is the book's recurring shape once
   more: the deterministic floor is necessary, not sufficient, and precision comes from a distinction
   the raw metric cannot fully make.

3. **The discriminator is data-structure-versus-object, and that is a semantic call the tool only
   approximates.** The 22→0 and 48→0 collapse is the honest headline: a plausible deterministic signal
   was almost entirely false positives until it was scoped by meaning. It is a compact, self-contained
   case of the whole method's argument — a metric that looks objective is only useful once a semantic
   boundary is drawn, and drawing it well is where the steward and the LLM layer earn their place.

## Honest limits

- **Data-only mode found 1 entity in requests and 0 in flask.** Both libraries model their domain as
  classes, so there is almost nothing for a data-contract detector to catch. The signal bites in
  dict-and-JSON-heavy code — data pipelines, service payloads, and much AI-generated glue — not in
  object-oriented library code. That is a scope statement, not a defect, but it must be stated.
- **The canonical shape is the union of keys seen across the codebase.** A dict used polymorphically
  (different keys in different contexts) inflates the denominator and can over-report under-use.
- **"Forwards whole" is the weaker half of the signal.** Without following the call it cannot tell
  wholesale delegation from genuine over-sharing; under-use of a non-forwarded entity is the more
  reliable flag.
- **Not promoted to a ratcheted signal.** On this evidence it belongs in the self-model's query surface
  as a diagnostic ("which sites are stamp-coupled to `order`?"), not in the multi-signal ratchet. It is
  a ranking lens for the steward, subject to the same precision limit as the other structural signals.

## Verdict

Stamp coupling joins connascence of meaning and the duplication clusters as a deterministic structural
signal that names an established antipattern — but only in its data-contract reading, and only as a
triage lens. The result worth keeping is the false-positive collapse itself: it is the clearest small
demonstration in the corpus that a deterministic coherence signal needs a semantic boundary to be worth
anything, which is the book's thesis in one experiment.
