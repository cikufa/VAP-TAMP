# Baseline acceptance report

**Current overall result: FAIL — acceptance evidence incomplete.**
No connector code has been implemented. No successful-baseline commit is claimed.

Scope: pipeline/method reproduction on an alternative released VAP-TAMP task
because the exact released Ihlen firewood task instance is absent from the
public artifact. Candidate: bringing_water / cached Wainscott_0_garden.
This is not exact task-level reproduction of the paper.

| Required gate | Result | Evidence / remaining work |
| --- | --- | --- |
| Simulator startup / minimal rendering | PASS, bounded checks | Inotify quota fixed via project watcher exclusion. Native RGB/physics, minimal OG and Rs_int scene checks pass; see renderer_fix.md |
| Five consecutive task startups | FAIL | Two passes, third fails in Isaac USD traversal during Fetch loading; series stopped. See camera_and_primitive_acceptance.md |
| Alternative released task loads | PASS, scene and cameras | bringing_water / Wainscott_0_garden reset and RGB/segmentation pass; see camera_and_primitive_acceptance.md |
| Scripted primitive | FAIL | Released lookat calls a Tiago-specific head helper on Fetch; KeyError head_1_joint. Action testing stopped here |
| Planner works | PASS, symbolic scope | Released wrapper yields 8 actions / 9 states; VAL certifies bringing_water plan |
| VLM works | FAIL (not demonstrated) | Exact gpt-4-turbo retained; OPENAI_API_KEY absent; no authenticated call |
| Predicates verified | FAIL (not demonstrated in simulator) | Extraction passes planner check; no real image/query evidence |
| State updates work | FAIL (not demonstrated end to end) | Released update code retained, event logging present; no live discrepancy |
| Replanning works | FAIL (not demonstrated end to end) | Planner smoke is not a discrepancy/recovery episode |
| Active perception works / faithfully reconstructed | FAIL | Fixed-view released sim retained; Algorithm 2 control-flow component tested; VLM/motion/observation integration remains pending |
| Full trial finishes | FAIL | No full trial launched |
| Video/logging works | FAIL (partial logging only) | Probe logs and JSON timings exist; no task video |

FAIL (not demonstrated) is an evidence gate, not evidence that the method is
scientifically ineffective. The prior startup failure is fixed; full VAP-TAMP acceptance remains separate.

## Evidence

- Missing artifact search: `missing_ihlen_instance_audit.md`.
- Exact VLM identifier/access status: `vlm_model_provenance.md`.
- Bringing-water symbolic trace:
  `results/original/planner_smoke/20260915T174443219747Z/summary.json`.
- Startup measurements: `results/original/startup/20260915T174130727503Z/summary.json`.
- Seven compatibility/security tests pass; these are unit tests, not simulation trials.

## Remaining acceptance sequence

1. Diagnose the third-launch Isaac USD traversal exception and establish five clean startups. Then resolve the Fetch/Tiago head-joint mismatch in lookat. Camera warm-up and observation-space refresh pass in completed loads.
2. Authenticate exact model and run one debug trial on the alternative released task.
3. Validate the general paper algorithm separately from the fixed-view release:
   five paraphrases, majority vote, sufficiency, VLM direction, actual new sensor
   observation, symbolic correction and replan. Do not label the dormant generic
   preset-view wrapper as Algorithm 2. Record unspecified parameters explicitly.
4. Run 3–5 complete trials with the released failure injection probabilities;
   retain all seeds/outcomes, capture actual state, raw visual queries and videos.
5. Require at least one real situation-handling trace. Use only the released
   injection mechanism if additional exercise is needed; no engineered failures.
6. Update this report with evidence and commit the passing baseline before any
   connector implementation.

## Checkpoint interpretation

The missing Ihlen file no longer blocks selection of an alternative released
task. Native material-system initialization is fixed by freeing the user inotify watch quota.
Camera/reset compatibility is fixed; the first scripted lookat primitive fails on a Tiago-specific helper used with Fetch. End-to-end acceptance and local VLM credentials remain outstanding. No full debug trial or 3–5-trial pilot can be claimed.
Twelve unit tests pass (seven compatibility/security, five paper control flow),
but all runtime algorithmic gates above remain unvalidated. No trial videos
exist. The requested passing-baseline commit must wait for actual evidence.

Final native cleanup check: no simulator or GPU compute processes remain. All
new probes reported zero changed files in monitored external NVIDIA/Omniverse
paths. No driver, system CUDA or other project was modified. Optional native
diagnostic settings did not resolve startup and are not baseline defaults.
