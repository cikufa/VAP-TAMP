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
| Five consecutive task startups | PASS with process affinity | Five task/camera/step/shutdown passes on CPUs 16–31; see startup_affinity_fix.md. Earlier failures retained |
| Alternative released task loads | PASS, scene and cameras | bringing_water / Wainscott_0_garden reset and RGB/segmentation pass; see camera_and_primitive_acceptance.md |
| Head lookat primitive | PASS | Fetch compatibility adapter validated against physical camera pose and joint limits; see fetch_head_compatibility.md |
| Task manipulation primitives | PASS, execution infrastructure only | Eight-action scripted replay completes; four navigation calls find valid poses and one bottle is grasped/placed. A second grasp fails its released visibility precondition; recovery needs the VLM loop |
| Planner works | PASS, symbolic scope | Released wrapper yields 8 actions / 9 states; VAL certifies bringing_water plan |
| VLM works | BLOCKED (model access) | Key authenticates successfully (model list HTTP 200), but exact gpt-4-turbo lookup and completion both return 404 model_not_found; see vlm_model_provenance.md |
| Predicates verified | FAIL (not demonstrated in simulator) | Extraction passes planner check; no real image/query evidence |
| State updates work | FAIL (not demonstrated end to end) | Released update code retained, event logging present; no live discrepancy |
| Replanning works | FAIL (not demonstrated end to end) | Planner smoke is not a discrepancy/recovery episode |
| Active perception works / faithfully reconstructed | FAIL | Fixed-view released sim retained; Algorithm 2 control-flow component tested; VLM/motion/observation integration remains pending |
| Full trial finishes | FAIL | No full trial launched |
| Video/logging works | PASS for scripted replay; VLM logging pending | First/third-person MP4s decode, with action/position traces. Full VLM episode artifacts still require access to the released model |

FAIL (not demonstrated) is an evidence gate, not evidence that the method is
scientifically ineffective. The prior startup failure is fixed; full VAP-TAMP acceptance remains separate.

## Evidence

- Missing artifact search: `missing_ihlen_instance_audit.md`.
- Exact VLM identifier/access status: `vlm_model_provenance.md`.
- Bringing-water symbolic trace:
  `results/original/planner_smoke/20260915T174443219747Z/summary.json`.
- Stable startup measurements: `results/original/startup/20260915T204931522467Z/summary.json`.
- Corrected task primitive replay: `results/original/startup/20260915T210243262027Z/summary.json`.
- Final replay/video/state-logging validation: `results/original/startup/20260915T210530389331Z/summary.json`; task result false is retained.
- Fifteen compatibility, geometry and paper-control-flow tests pass; these are not VLM trial evidence.

## Remaining acceptance sequence

1. Resolve exact-model access: the supplied key authenticates, but both model lookup and direct completion return `404 model_not_found` for `gpt-4-turbo`. Use a credential/project with access, or obtain explicit approval for a documented model deviation. Evidence: `results/original/model_access/20260915T214338284812Z/endpoint_diagnosis.json`.
2. Once exact-model access works (or a deviation is approved and verified), run one debug trial on the alternative released task, diagnosing any newly exposed verification/replanning issue before a pilot.
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
Camera/reset and Fetch lookat compatibility are fixed. The floor navigation
sampler now uses actual AABB side faces. Eight-action scripted execution and
videos work, including a real unsuccessful grasp that the untested VLM loop
must detect/recover from. No full VLM debug trial or 3–5-trial pilot is claimed.
Fifteen unit tests pass. The requested passing-baseline commit must wait for
authenticated, end-to-end evidence.

Final native cleanup checks: no probe simulator processes remain. All
new probes reported zero changed files in monitored external NVIDIA/Omniverse
paths. No driver, system CUDA or other project was modified. Optional native
diagnostic interpreter/thread changes did not resolve startup. Process affinity
is the validated default on this machine; see `startup_affinity_fix.md`.
