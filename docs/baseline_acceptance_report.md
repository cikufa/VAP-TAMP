# Baseline acceptance report

**Current overall result: FAIL — acceptance evidence incomplete.**
No connector code has been implemented. No successful-baseline commit is claimed.

Scope: pipeline/method reproduction on an alternative released VAP-TAMP task
because the exact released Ihlen firewood task instance is absent from the
public artifact. Candidate: bringing_water / cached Wainscott_0_garden.
This is not exact task-level reproduction of the paper.

| Required gate | Result | Evidence / remaining work |
| --- | --- | --- |
| Simulator stable | FAIL | 0/5 sequential launches pass; 900 s fresh-cache and import-order follow-ups also fail (startup_stability_report.md) |
| Original/released task loads | FAIL (not demonstrated) | Supplied cached task exists and object names match PDDL; scene loading not reached |
| Planner works | PASS, symbolic scope | Released wrapper yields 8 actions / 9 states; VAL certifies bringing_water plan |
| VLM works | FAIL (not demonstrated) | Exact gpt-4-turbo retained; OPENAI_API_KEY absent; no authenticated call |
| Predicates verified | FAIL (not demonstrated in simulator) | Extraction passes planner check; no real image/query evidence |
| State updates work | FAIL (not demonstrated end to end) | Released update code retained, event logging present; no live discrepancy |
| Replanning works | FAIL (not demonstrated end to end) | Planner smoke is not a discrepancy/recovery episode |
| Active perception works / faithfully reconstructed | FAIL | Fixed-view released sim retained; Algorithm 2 control-flow component tested; VLM/motion/observation integration remains pending |
| Full trial finishes | FAIL | No full trial launched |
| Video/logging works | FAIL (partial logging only) | Probe logs and JSON timings exist; no task video |

FAIL (not demonstrated) is an evidence gate, not evidence that the method is
scientifically ineffective. Startup failures precede VAP-TAMP execution.

## Evidence

- Missing artifact search: `missing_ihlen_instance_audit.md`.
- Exact VLM identifier/access status: `vlm_model_provenance.md`.
- Bringing-water symbolic trace:
  `results/original/planner_smoke/20260915T174443219747Z/summary.json`.
- Startup measurements: `results/original/startup/20260915T174130727503Z/summary.json`.
- Seven compatibility/security tests pass; these are unit tests, not simulation trials.

## Remaining acceptance sequence

1. Resolve and repeat sequential startup/scene/camera checks.
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
task. The current blockers are native material-system initialization and absent
local VLM credentials. No full debug trial or 3–5-trial pilot can be claimed.
Twelve unit tests pass (seven compatibility/security, five paper control flow),
but all runtime algorithmic gates above remain unvalidated. No trial videos
exist. The requested passing-baseline commit must wait for actual evidence.

Final native cleanup check: no simulator or GPU compute processes remain. All
new probes reported zero changed files in monitored external NVIDIA/Omniverse
paths. No driver, system CUDA or other project was modified. Optional native
diagnostic settings did not resolve startup and are not baseline defaults.
