# Paper active perception: implementation boundary

## Three distinct components

A. **Exact released simulation behavior:** one batched predicate query per view,
current effects plus successor preconditions, GT handling for specified predicates,
symbolic correction and replanning. The default remains fixed-view relative to the
base, matching Section V-B. Compatibility fixes do not enable the dormant AP hook.

B. **General paper mechanism:** Algorithm 2 asks five paraphrases on the same image,
uses binary majority, checks sufficiency only after high agreement, requests a
VLM direction when unresolved, navigates, observes and refreshes the graph.
This is distinct from the published fixed-view simulation experiment.

C. **Missing integration:** an OG camera/motion adapter and observation-to-symbolic
refresh connected to B, with actual VLM calls and event logs. The existing generic
real-robot preset-view module is not such an adapter. C remains unvalidated and
is not switched on merely by exposing an environment flag.

## Implemented control flow

`vlm-tamp/paper_verification.py` implements Algorithm 2 as a small function with
explicit VLM, movement, observation and graph-refresh dependencies. It has no
planner-wide knowledge, successor input, view score, NBV objective, information
gain or connector logic. Five scripted callback tests verify call order, same-image
votes, insufficient-view reacquisition, majority, budget exhaustion and rejection
of nonbinary responses. These tests are not VLM or simulator evidence.

The function is deliberately not advertised as a working simulation integration.
In particular, supplying a no-op graph update or fake movement would not pass
baseline acceptance. No adapter of that kind is used in an experiment.

## Unspecified parameters and literal pseudocode behavior

- N=5 and strict majority are specified by the paper.
- Numerical consistency threshold is unspecified. Callers must explicitly supply
  4 or 5 agreeing votes; no implicit default is claimed to come from the paper.
- K is unspecified and must be explicitly supplied.
- The printed loop runs k=0 through K inclusive and navigates even on its final
  unresolved iteration, then returns the preceding vote. The component preserves
  that literal behavior (K+1 possible motion attempts). Its return value distinguishes
  the voted observation from the terminal unvoted observation. This avoids silently
  changing the pseudocode or associating a vote with a different image.
- Invalid/nonbinary responses raise a data-quality error; they are never converted
  into affirmative facts. The paper assumes binary responses and does not specify
  recovery from malformed API output. This is an explicit handling assumption.
- Direction-to-metric-motion magnitude, infeasible-direction behavior and the
  observation refresh implementation require documented embodiment choices and
  real camera/robot checks before the adapter can be accepted.

Remaining sequence: load the released alternative task, validate sensors and native
motion, connect the exact appendix prompts and model, then test the complete loop
in a real situation-handling trial. Do not mark the active-perception gate PASS
from control-flow unit tests. No connector implementation is permitted yet.

Source: [paper Section IV-B, Algorithm 2 and Appendix I](https://arxiv.org/html/2604.26988v1).
