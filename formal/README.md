# Formal-methods lab

This lab keeps three evidence claims separate:

- `FORMALLY_VERIFIED_IMPLEMENTATION` applies only to the Dafny implementation in this directory and
  the stated contracts that Dafny verifies.
- `MODEL_CHECKED` applies only to the finite TLA+ checkout-contract rollout model and its stated
  safety and liveness properties.
- Neither result proves the behaviour of the Python reference tool or an enterprise production
  service. Those implementations need their own traceable link to a verified artefact.

Run `./verify.sh` with `DAFNY` and `TLA2TOOLS` pointing to Dafny 4.11.0 and TLA+ tools 1.7.1. The
script expects the faithful Dafny implementation and safe rollout model to pass. It also expects the
rounding mutation and unsafe rollout to fail, demonstrating that both tools can reject the known
defects.

The lab uses integer milli-cents and integer discount basis points. This removes floating-point
behaviour from the property being proved. The TLA+ state space contains two consumers and two
contract versions. Weak fairness is required for the liveness property; the safety invariant does
not depend on that fairness assumption.

## Reproduce

```sh
DAFNY=/path/to/dafny \
TLA2TOOLS=/path/to/tla2tools.jar \
./verify.sh
```

`manifest.json` records tool versions, hashes, properties, assumptions, and observed results from the
verified run. Recompute it after changing any formal artefact.

