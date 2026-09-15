# Camera acceptance and first primitive failure

**Latest update:** camera and head compatibility are fixed; five sequential
task startups pass with process affinity. The scripted task primitives now
execute with genuine failure outcomes retained. See `startup_affinity_fix.md`,
`fetch_head_compatibility.md`, and `released_primitive_replay.md`. The failures
below are the preserved diagnostic history, not the current status.

2026-09-15. Alternative released task: `bringing_water`, cached
`Wainscott_0_garden`, Fetch. This is pipeline reproduction, not exact Ihlen
firewood reproduction. No full episode or connector experiment was run.

## Camera/reset compatibility fix

The cached robot configuration bypasses the requested YAML modalities. After
adding the segmentation required by the released code, OG 1.0 needs two explicit
initialization steps:

1. `env.load_observation_space()` refreshes the environment and robot spaces.
2. Ten `og.sim.render()` calls populate the new annotators without physics steps.

These steps are in the probe and evaluator. Neither substitutes synthetic
pixels nor disables observation-space validation.

Evidence, under `results/original/startup/`:

| Run | Changed variable | Result |
| --- | --- | --- |
| `20260915T200421968553Z` | Render warm-up | Empty segmentation fixed; reset then reports stale observation space |
| `20260915T200511003127Z` | Refresh observation space | PASS: reset, ten simulation steps, RGB and both segmentations, clean shutdown |
| `20260915T200622866038Z` | Invoke released `lookat` after camera acceptance | Camera PASS; primitive FAIL as below |

The task camera returns RGB 128×128×4, semantic segmentation 128×128, and
instance segmentation 128×128. The probe checks nonempty finite image values.
RGB PNGs, source snapshots, tracebacks, Kit logs and phase timings are retained.

## First failing primitive layer

The probe extracts `lookat` from the evaluator's AST and executes that function
unchanged with the real task, Fetch and `StarterSemanticActionPrimitives`.
This avoids the evaluator's module-level credential requirement. It records
the function hash; it does not emulate a VLM or modify the released action.

The exact failure is:

```
eval.py:lookat
  ap._get_head_goal_q(target_obj_pose)
OmniGibson starter_semantic_action_primitives.py:1280
  self.robot.joints["head_1_joint"]
KeyError: 'head_1_joint'
```

That private OG helper hard-codes Tiago `head_1_joint`, `head_2_joint`, and
`head_2_link`, despite the primitive class supporting Fetch as well. Fetch uses
head pan/tilt joints and links. The released evaluator also negates the returned
angles, so blindly renaming joints is insufficient to establish correct motion.
`goto`, placement, and drop code call `lookat`; this is relevant to execution.

Action testing stopped at this layer. A compatibility adapter must validate
Fetch joint order, rotation signs, limits, and actual camera response before
continuing. No manipulation or active-perception success is claimed.

## Credentials and remaining gate

A presence-only check still found no `OPENAI_API_KEY` in the environment or
project `.env`. The private `configure_openai_key.py --check` helper is available
but does not create an account credential. No authenticated request was sent.
The released model was `gpt-4-turbo`. The current reproduction uses the
user-approved pinned `gpt-4o-2024-05-13` deviation; see
`vlm_model_provenance.md`.

All 12 existing compatibility and paper-control-flow unit tests pass. These
do not establish live VLM, manipulation, replanning or full-trial acceptance.

## Sequential stability series

`results/original/startup/20260915T200657962867Z`: requested five launches; stopped after the third failed. This does **not** pass the five-launch stability gate.

| Probe | Result | Wall seconds | GPU before/after MiB | Cleanup / external writes |
| --- | --- | --- | --- | --- |
| 1 | PASS | 24.22 | 1584 / 1625 | 0 simulator processes; 0 changed monitored files |
| 2 | PASS | 24.24 | 1625 / 1592 | 0 simulator processes; 0 changed monitored files |
| 3 | FAIL | 18.18 | 1592 / 1608 | 0 simulator processes; 0 changed monitored files |

Probe 3 initialized the renderer in the normal time, then failed loading the Fetch dummy asset. The traceback ends in bundled Isaac `utils/prims.py:get_all_matching_child_prims`, line 359, at `traversal_queue.pop(0)`, with `AttributeError: str object has no attribute pop`. The source initializes that local as a list and only concatenates lists; source inspection alone does not explain the observed type. Do not attribute this to the driver, cache, or VAP-TAMP without further evidence. All three processes shut down cleanly. GPU totals include desktop activity; this short series cannot establish absence of a long-term leak.

Next simulator diagnostic: capture the failing helper’s runtime code identity and local variable types during task construction in a bounded instrumented launch. Preserve the original failed attempt. The separate Fetch head-helper mismatch remains unresolved.
