# Original reproduction status

Last updated 2026-09-15. **Stage A is not yet reproduced.** No connector code
may be started from this checkpoint.

## Completed verification

- Clean official clone, dedicated branch, pinned upstream SHA.
- Source audit of simulation, real-robot wrappers, planner/validator integration,
  scene graph code, paper and prompt appendix.
- Dedicated Conda prefix with Python 3.10.21 and pddl 0.4.2 (see actual export
  for authoritative versions). No reuse of base or an existing research environment.
- Fast Downward and VAL built from the vendored sources without source changes.
- `scripts/planner_smoke.py` passes on unmodified `store_firewood` PDDL using
  the released `pddlsim` wrapper: eight plan actions, nine intermediate states,
  parsed grounded preconditions/effects, both symbolic goals satisfied, VAL valid.
- A second smoke run after clearing inherited ROS PYTHONPATH also passes.

Example artifact directory:
`results/original/planner_smoke/20260915T171250121202Z/`.
It contains `pddl_output.txt`, `val.txt`, `summary.json`, `wrapper_stdout.txt`.
These are symbolic planning artifacts, not debug-episode artifacts.

The original plan collects stick 3, places it on the table, collects stick 2,
and places it on the table. Each object transfer uses find/grasp/find/placeon.
The unused third grasp parameter grounds to the agent; this is allowed by the
released domain and is not evidence of a robot grasp implementation.

## Gates still required

| Gate | Status |
| --- | --- |
| Historical engine/source available | Verified native layer from official OG 1.0.0 image; extracted locally |
| Exact native torch/CUDA compatibility | Python 3.10, torch 2.0.1+cu118, vision 0.15.2+cu118; GPU arithmetic passes |
| Dataset download permission | User approved 22.32 GB bundle, conditional on compatibility and disk checks |
| Asset installation, task membership | Dataset/assets extracted and verified; required Ihlen firewood instance absent (see asset_status.md) |
| OpenAI credential, exact-model API call | OPENAI_API_KEY absent at audit; no API test |
| OmniGibson launch and camera | Two contained native launches pass; later startup stalled; task/camera not validated |
| Original episode / five trials | Not attempted |
| Successful original baseline commit | Does not exist |
| Moving-view method validation | Not implemented |
| Connector diagnostic / videos / counterfactuals | Not started |

No numerical experimental result about the handoff hypothesis is available.

## Re-run the completed check

```bash
cd /home/shekoufeh/VAP_TAMP/VAP-TAMP-clean
source scripts/project_runtime.sh
bash scripts/build_planners.sh
.runtime/envs/vaptamp-repro/bin/python scripts/planner_smoke.py
```

The source script is for Bash. Start `bash` first if using a Zsh terminal.
The smoke creates a new result directory; it does not overwrite prior runs.

## Compatibility work before original episodes

1. Completed: avoid `eval.py`'s eager optional Gemini import / Vertex constructor side effect.
2. Completed: parameterize seed, trial count, output path and the existing baseline flags;
   use classical planning + both checks + predicate queries for the requested baseline.
3. Completed: replace recursive output deletion with unique run directories.
4. Completed: fail visibly on VLM transport/API failure instead of manufacturing affirmative
   predicate answers; retain exact prompt, endpoint and successful response semantics.
5. Unit/source validation passes; original-scene validation pending: validate Fetch observation shape, sensor modalities, object-instance mapping,
   BDDL activity names and object aliases against the pinned OG candidate.
6. Pending: capture raw inputs/outputs, simulator state and VLM query events with explicit
   provenance. Preserve injection probabilities and released verification order.

The attachment ends mid-sentence in Section 26. Remaining instructions were
requested and are pending; do not infer omitted evaluation requirements.

The first native launch crashed and wrote five external NVIDIA logs. The next
two launches passed with structured-log redirection; external log sizes and
timestamps did not change. See `compatibility_fixes.md` for the incident and limits.

The user requires the paper setup, so the supplied Merom firewood instance has
not been substituted. The paper does not name a scene ID; release default
Ihlen is the available source evidence. See `asset_status.md`.

An opt-in trace now records exact VLM request bodies (including encoded input
images), response bodies/statuses, plans, verification inputs/outputs, symbolic
updates and action boundaries. Authorization headers are never recorded.
This instrumentation has not yet been exercised in a real episode; physical
state snapshots, video assembly and full metric validation remain pending.

## Revised validation scope (after c28bf5b)

The user now authorizes method/pipeline validation on an alternative released
task after a brief exhaustive public-artifact search. That search is complete:
`missing_ihlen_instance_audit.md`. The default Ihlen configuration remains intact;
Merom is not substituted. `bringing_water` with the supplied Wainscott cache is
selected as the alternative candidate, with explicit initialization deviation.
Its unchanged PDDL passes an 8-action / 9-state VAL-validated planner check.

Five sequential startup attempts all exceeded 120 s before scene loading.
See `startup_stability_report.md` for timestamps, GPU measurements, cleanup,
native debugger traces and the longer warmup investigation. There is still no
successful scene/camera or full task episode. OpenAI key remains absent.

`paper_verification.py` now implements and unit-tests the general Algorithm 2
control flow; real VLM/motion/observation integration is not yet validated.
This is separate from the released fixed-view simulation and is not enabled
in the baseline launcher. See `paper_active_perception_integration.md`.

The authoritative acceptance gate is `baseline_acceptance_report.md` (currently
FAIL). Neither an acceptance commit nor connector implementation exists.
