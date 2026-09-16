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

C. **Reconstructed integration:** `paper_sim_adapter.py` connects B to native OG
camera/motion, RGB-D instance memory and the released symbolic updater. Its live
Gemini episode executed five view changes and continued after discrepancies.
The [episode report](paper_adapter_episode_results.md) distinguishes this observed
chain from full trial completion, which was blocked by daily quota. The existing
generic real-robot preset-view module is not used for this adapter.

## Implemented control flow

`vlm-tamp/paper_verification.py` implements Algorithm 2 as a small function with
explicit VLM, movement, observation and graph-refresh dependencies. It has no
planner-wide knowledge, successor input, view score, NBV objective, information
gain or connector logic. Scripted callback tests verify call order, same-image
votes, insufficient-view reacquisition, majority, budget exhaustion and rejection
of nonbinary responses. These tests are not VLM or simulator evidence.

The standalone callback tests alone do not establish simulation integration.
The optional native adapter additionally has real RGB-D, movement, five-query
voting and replanning evidence. Its [documented assumptions](paper_sim_adapter.md)
include compact object memory rather than a full voxel-map pipeline.

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

Remaining acceptance item: complete a bounded episode on the current adapter
revision after Gemini quota reset. The general recovery chain is now observed
live, but an interrupted episode is not a completed trial. The model/provider and
embodiment substitutions remain explicit. No connector implementation has begun.

Source: [paper Section IV-B, Algorithm 2 and Appendix I](https://arxiv.org/html/2604.26988v1).
