# Released bringing_water primitives: isolated replay

This diagnostic loads the cached Wainscott task with Fetch, runs Fast Downward
and VAL on the released PDDL, then calls the released find/grasp/place-on-floor
functions in plan order. It omits the VLM client and verification loop entirely.
It is **not** a full VAP-TAMP episode or a scientific trial.

`scripts/released_actions_smoke.py` extracts evaluator definitions via AST to
avoid its module-level episode execution. It retains the released task's
2.0 m grasp-height override, false oracle flag and action-failure probabilities.
Seed 0 applies to diagnostic action draws; this does not establish full physics
determinism or equivalence to the evaluator's initialization sequence.

## Additional compatibility fixes

* OG 1.0 exposes semantic labels through `semantic_class_id_to_name()` instead
  of the unavailable `CLASS_NAME_TO_CLASS_ID` constant. The evaluator now uses
  that function. All top-level imports pass without constructing a VLM client.
* OG's `_sample_position_on_aabb_side` used full bounding-box extent as the
  center-to-face distance. `EntityPrim.aabb_extent` is explicitly max minus
  min, so the correct distance is half the extent. For the kitchen floor the
  old helper placed samples outside the room and all 1,000 attempts failed.
  The project-local `primitive_compat.sample_aabb_side` corrects only this
  factor, retaining the same axis/direction/random-coordinate sampling, room
  checks, collision checks and candidate budget. Geometry tests require both
  floor-sized and small-object samples to lie on actual side faces.

These are class-B implementation compatibility corrections. No planner
objective, verification order, active-perception trigger or failure probability
was changed.

## Preserved evidence

All run IDs below are under `results/original/startup/`.

| Run | Result |
| --- | --- |
| `20260915T205657863317Z` | Rejected: unavailable semantic-label constant during evaluator import |
| `20260915T205830223895Z` | Eight calls return, but both floor navigations fail. Released height/tracker-based goal heuristic returns true anyway. **Not** accepted as valid navigation or VAP-TAMP success |
| `20260915T210243262027Z` | Corrected geometry: all four find calls return true, first bottle is held and placed in the kitchen; second grasp fails visibility and subsequent placement returns without holding an object. Eight calls finish and shutdown succeeds |
| `20260915T210530389331Z` | Final validation with shared video encoder and full simulator-state logging: same execution outcome, explicit released_goal=false, 11 decoded frames in each video, clean exit |

The corrected replay preserves that failed grasp. It does not add a retry,
extra camera motion, oracle answer or fabricated symbolic state to force task
success. The full VLM loop must demonstrate whether it detects and recovers
from such a discrepancy once credentials are supplied.

The release calls `tuck()` after `lookat()` within navigation; this can restore
the fixed head pose. That behavior remains unchanged. A pointable head alone
does not imply the final action observation shows the target.

## Artifacts and interpretation

Each replay records planned actions, action returns, object poses, held-object
and floor trackers, rendered frames, and first/third-person MP4s. Generated
artifacts stay Git-ignored. Video playback is an observation sequence at
12 FPS, not a real-time rendering of simulation duration; frame events record
simulation timestamps. The shared encoder verifies every frame decodes.

The full episode launcher now also assembles videos, preserves the released
goal results, and requires the requested number of `trial_end` events before
accepting process completion. Process exit alone is insufficient.

Next gate: user-supplied `OPENAI_API_KEY`, exact `gpt-4-turbo` access, then one
bounded full debug episode. Only its live visual predicates, state updates,
replanning and final result can establish VAP-TAMP baseline acceptance.
