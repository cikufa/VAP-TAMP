# Fetch base-planning copy self-collision

The first full paper-adapter episode (`20260916T010749710787Z`) requested
inspection directions but rejected three paths. It was deliberately stopped
for diagnosis, retaining incomplete logs/videos and `diagnostic_stop.json`.
SIGTERM did not finish promptly; the episode group was killed and reaped.

## Exact blocking operation

The 38.4-second isolated native probe
`results/original/startup/20260916T011312097009Z` replayed the recorded pose and
queried the same collision interface, without VLM calls. Both the first path
sample and the unchanged standing pose reported the same pair:

- `/World/robot_copy/torso_lift_link`
- `/World/robot_copy/elbow_flex_link`

This was internal overlap in the planning copy, not an environment obstacle.
OG's `PlanningContext(..., "simplified")` falls back to an original copy when
the requested representation is unavailable. Its blanket self-collision filter
is applied only when the resolved type is still simplified. The Fetch fallback
therefore loses the requested base-planning semantics.

## Project-local correction

`ignore_copy_self_collisions` applies the same copy-only filter that OG already
uses for a simplified copy. Both base-pose sampling and optional inspection-path
checking call it after constructing their base-only planning context. Posture
does not change along these candidate base paths. Existing environment filters
remain unchanged; no wall/object collision filter is disabled.

This is an execution compatibility correction, not a new VAP-TAMP planning or
sensing objective. It can change accepted poses and subsequent random draws.
The earlier fixed-view pilot predates this correction and is labelled accordingly;
do not silently treat its outcomes as measurements of this new code revision.

## Native regression evidence

`results/original/startup/20260916T011553267992Z`, 40.4 seconds:

- Same recorded native pose and the previously selected front direction.
- Without the copy-only filter: rejected on the internal torso/elbow pair.
- With the filter: requested path accepted and robot moved about 0.24 m.
- New camera image hash; target bottle newly represented by 77 depth/instance
  pixels and object memory refreshed from those real measurements.
- No VLM requests or artificial task failure injection in this regression.
- Clean process cleanup and zero changes in monitored external Omniverse paths.
- 28 local tests pass, including preservation of environment collision rules.

Next declared test: repeat the full optional paper-adapter debug episode, seed 6,
same K=2, agreement 4/5, 0.25 m displacements, unchanged prompts/model and failure
probabilities. Use a 1,200-second episode bound to accommodate five-query rounds
at the observed 15-request/minute quota. This is a bounded episode with stage
progress, not a renderer-startup wait. Preserve both attempts separately.
