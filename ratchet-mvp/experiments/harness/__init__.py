"""A dispatcher for the language-model probes, so a recorded run becomes a re-runnable one.

Forty-three of this directory's sixty-two write-ups are recorded runs: fully documented, and not
mechanically re-runnable, because the trial fixtures lived in a session scratchpad and the prompts
and model identity were never committed. The probes were never the problem. Several of them already
expose exactly the right interface — a `build_prompt(condition)` that embeds a committed fixture, and
a deterministic `score_code(...)` with no model in the loop. What was missing was the middle: dispatch
N trials to a pinned model, persist the raw responses, and stamp what produced them.

This package is that middle, written once for every probe rather than inside one of them.

Two properties decide whether a promoted write-up is worth anything.

**The model is pinned to a dated snapshot, and an alias is refused.** A run against
`claude-haiku-4-5` is not reproducible, because the name will point at something else later and the
comparison silently becomes cross-model. The dispatcher requires a dated identifier and says so.

**Raw responses are committed, so scoring can be re-run offline for ever.** A model snapshot is
eventually retired, at which point re-generation is impossible and re-scoring is the only check left.
Persisting the raw response means a reader can dispute the scorer without an API key, and a scorer
change can be re-run against the original evidence — which is what a deterministic scorer is for.

That is why a promoted entry is `PINNED_MODEL_RUN` rather than `REPRODUCIBLE_FIXTURE`, and why its
write-up says "reproducible-as-recorded" and never "reproducible". A sampled model is not a
deterministic fixture, and the class must not pretend otherwise.
"""

from .dispatch import (  # noqa: F401
    DispatchRefused,
    Manifest,
    ProbeContract,
    anthropic_transport,
    openai_transport,
    dispatch,
    load_probe,
    rescore,
)
