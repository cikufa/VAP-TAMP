# Bringing-water fixed-view pilot plan

Declared before running seeds 1, 2 and 3 on 2026-09-16 UTC.

- Three independent processes, one complete requested trial each, seeds 1/2/3.
  Previously completed seed 0 remains a debugging run and is not pooled.
- 600-second wall-clock bound per process; released 50-action bound unchanged.
  Structural failures stop the series for diagnosis; retain every attempt.
- Gemini `gemini-3.5-flash-lite`, original prompts, 256x256 images, released
  parsing, full precondition/effect verification, PDDL planning, fixed camera
  relative to base, original stochastic primitive probabilities.
- Cached Wainscott_0_garden bringing_water instance, OG 1.0 / Isaac 2023.1.1.
  CPUs 16–31, project runtime/caches, no host-stack changes.
- This is a provider/model and scene substitution, not exact reproduction.
- Preserve released score unchanged. Also log settled object geometry, physical
  OnTop(target floor), room identity, and native BDDL goal evaluation separately.
  Native BDDL asks for bottles inside the cabinet, whereas the released PDDL
  asks for bottles on floor.n.01_1; these are different goals.
- Log all outcomes, raw image requests/responses, replanning traces and videos.
  Three seeds provide an execution pilot, not a reliable success-rate estimate.
- Only added observation is evaluation logging after settling. It does not feed
  privileged state into the VLM or planner. Close saved Matplotlib figures to
  prevent resource accumulation without changing generated images.

Hypothesis: the released origin-height proxy (z < 0.1 m) can reject an upright
~0.28 m bottle on the correct floor. Seed 0's last action records centers near
0.14 m; it lacks a final settled native predicate report, so this is not yet a
confirmed explanation for that seed.

## Amendment before seed 3

Seeds 1 and 2 both completed but failed after 51 actions (the released check is
`action_counter > 50`, so the operational maximum is 51). Seed 2 encountered
43 exhausted navigation searches after a bottle entered the kitchen. OG's
`in_rooms` remains its initial `garden_0` annotation. The helper incorrectly
requires candidate poses near the moved bottle to belong to that old room.

Stop the initial series after these two retained trials. Validate a correction
using an isolated replay of the saved moved-bottle pose, same RNG seed for the
old and corrected room rules. Then run a new three-trial series with seeds
3, 4, 5, same 600-second bound and all other settings above. Do not pool the
two conditions. The only execution change is current map-room lookup for
movable objects; retain fixed-object room annotations. Record the correction
as an execution/fidelity deviation even though it repairs stale metadata.
