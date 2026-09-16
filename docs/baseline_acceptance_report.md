# Baseline acceptance report

Updated 2026-09-16 UTC. **Fixed-view pipeline: PASS with documented deviations.
General moving-view recovery: observed live. Full episode on the latest adapter
revision: blocked by Gemini daily quota; overall connector gate not yet passed.**

Scope: pipeline/method reproduction on bringing_water because the exact released
Ihlen firewood task instance is absent from the public artifact. Cached scene:
Wainscott_0_garden. Gemini 3.5 Flash-Lite replaces the released OpenAI gpt-4-turbo.
This is not exact task/model reproduction or a replication of published success rates.

| Required gate | Result | Evidence |
| --- | --- | --- |
| Simulator stable | PASS | Five consecutive startup checks plus five new complete episodes; project affinity/runtime fixes retained |
| Released task loads | PASS, scene deviation | Cached bringing_water instance loads with Fetch and sensors |
| Planner works | PASS | Fast Downward/VAL plans and state replay used throughout all five episodes |
| VLM works | PASS, provider/model deviation | All five fixed-view episodes completed live Gemini image queries; bounded quota retries succeeded |
| Predicates verified | PASS | Original precondition/effect checks retained; no malformed or skipped batches in the five episodes |
| State updates work | PASS | Actual discrepancies changed symbolic states and rewritten PDDL problems |
| Replanning works | PASS | 33/48/39/26/43 planner calls in seeds 1–5; continuation after failures recorded |
| Active-perception mechanism | PASS for the documented reconstruction boundary | Five live VLM-directed motions, real new observations, re-voting, symbolic correction and continued planning; see the separate AP episode report |
| Full trial can finish | PASS fixed-view; FAIL/incomplete on latest moving-view revision | Five fixed-view trials completed. Latest AP episode stopped after 8 actions on daily quota, with no trial_end or final score |
| Video/logging works | PASS | Five pairs of decoded videos, raw prompts/images/responses, action/state traces and final physical predicates; separate AP observation videos supported |

FAIL here means an acceptance item remains unproven, not that the method is
scientifically ineffective. No connector code has been implemented, and no
all-core passing baseline commit is claimed yet.

## Completed fixed-view pilot

See [pilot results](bringing_water_pilot_results.md) for the predeclared conditions,
all seeds, failures, timing, commits and artifact paths. Machine-readable summary:
`results/original/pilot/20260916_bringing_water/summary.json`.

- Initial series: seeds 1 and 2, both completed and failed physically.
- Room-corrected series: seeds 3, 4 and 5, all completed; physical goal PASS/PASS/FAIL.
- Seed 4 completed its plan after 32 actions with no final verification mismatch.
- The released Python height score was false in all five trials. Native OnTop
  predicates demonstrate the two physical successes; this separate metric does
  not overwrite the historical output. Native BDDL's cabinet goal is different.
- These trials predate the later planning-copy self-collision repair. Do not
  treat them as outcome measurements of that later revision or pool conditions.

## Repairs and current method limits

- [Moved-object navigation](moved_object_navigation_fix.md): a bottle kept its
  cached garden label after being carried indoors. Current room lookup repairs
  that execution failure for movable objects.
- [Goal scoring](bringing_water_goal_scoring.md): the origin-height proxy rejects
  upright bottles on the correct floor and can accept fallen bottles elsewhere.
  Both scores are retained; assets and poses were not changed to improve scoring.
- [Base copy collision](base_copy_collision_fix.md): Fetch falls back to an
  original planning copy, losing simplified-copy self filtering. Native evidence
  identified a torso/elbow self-overlap; copy-only filtering restored movement.
- [Shallow lawn contact](lawn_support_collision_fix.md): a separate native replay
  validates the optional adapter's bounded support tolerance. Existing ground
  contact clears with a 1 cm raised copy; the real robot keeps its commanded height.
- [Optional paper adapter](paper_sim_adapter.md): five paraphrases, majority,
  sufficiency, VLM directions, real sensors and symbolic updates are separately
  implemented. K, consistency threshold, metric motion and compact object memory
  are documented reconstruction assumptions. Gemini enum formatting is an
  additional provider adaptation. It is not the released fixed-view experiment
  or a complete reconstruction of the paper's voxel-map generation stack.

Original primitives still use the release's kinematic/magic manipulation and
privileged state boundary. No physical grasp-planner equivalence is claimed.
The released effect/successor-precondition ordering remains explicit.

## Next acceptance step

The [moving-view episode report](paper_adapter_episode_results.md) records the
entire live recovery chain and the quota failure. It made 112 logical requests;
111 succeeded, and the final request exhausted the project's 500/day allowance.
All artifacts remain intact, and the simulator process group has exited.

Once the daily quota resets, repeat that bounded seed-6 episode from its initial
state with the same model and settings. The fail-fast quota repair avoids futile
short retries. Full latest-revision completion is the remaining acceptance item;
do not call the incomplete run successful or silently switch models to finish it.
Commit the accepted baseline before any connector diagnostic. Do not tune the
baseline to make the handoff hypothesis true.

No driver, system CUDA, Vulkan, system package or working GoFlow installation
was changed. Native regression probes reported zero changes to monitored external
Omniverse paths. Project run artifacts retain process cleanup evidence.

Final offline checks: 30 unit tests pass; all four moving-view episode videos
decode and all 18 HTML vote images resolve. Prompt-file handles now close explicitly
without changing their contents. This is a reproducible progress checkpoint,
not the all-core accepted baseline commit required before connector work.
