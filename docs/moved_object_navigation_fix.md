# Navigation recovery after an object changes rooms

## Observed failure

Bringing-water seed 2 (`results/original/debug_episode/20260916T003151131775Z`)
completed with a failed released score after 51 actions. It exhausted 43
navigation searches. Bottle 2 had moved to approximately (-6.65, 6.10, 0.071)
in kitchen_0, but its cached `in_rooms` still contained garden_0.

In the pinned OG 1.0 `DatasetObject`, `in_rooms` returns `_in_rooms`, initialized
from the cached scene. It is not a live localization query. The only other
assignment found under `omnigibson/` is initial BDDL sampling. The released
navigation helper uses this static label when filtering candidate poses.
Consequently a bottle carried indoors can become unreachable by that helper.

## Correction and fidelity

`navigation_target_rooms` now uses the current segmentation-map room at a
movable object's position. Fixed objects retain their annotated room sets;
this matters for large floors spanning several map segments. Unmapped movable
objects remain unresolved, without falling back to the stale room.

This repairs execution's use of room metadata. It changes which navigation
poses can be accepted and therefore can change later random draws and outcomes.
It is an explicitly documented execution deviation from the release, not an
exact-byte reproduction. It adds no sensing objective or successor reasoning.
VLM prompts, parsing, action probabilities, action limit and scoring are unchanged.

## Isolated native validation

Evidence: `results/original/startup/20260916T003852433468Z/summary.json` and
`probe_1/phases.jsonl`. Replayed only the real trial's recorded bottle pose;
this is a geometry regression fixture, not a scientific failure injection.

- Same native cached scene, object model, collision checker, and RNG seed 0.
- Old room rule: no pose after 1,000 candidates.
- Corrected rule: a collision-free candidate in kitchen_0.
- Probe finished in 40.4 s, clean shutdown, no remaining simulator processes,
  and zero changes to monitored external Omniverse files.
- 21 local tests pass, including movable-object relocation, fixed multi-room
  floor handling, and out-of-map behavior.

Seeds 1 and 2 are retained as the initial series. The amended pilot predeclares
seeds 3, 4 and 5 under this correction, reported separately.
