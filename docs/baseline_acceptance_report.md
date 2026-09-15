# Baseline acceptance report

**Current overall result: PARTIAL PASS — one bounded end-to-end pipeline trial
completed; scientific acceptance and multi-seed estimates remain incomplete.**
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
| VLM works | PASS (provider/model deviation) | Gemini free-tier image requests pass; active Gemini 3.5 Flash-Lite preserves prompts/input/parsing through a modular adapter. See gemini_backend_substitution.md |
| Predicates verified | PASS (Gemini deviation) | 41 live image requests and 61 verification events completed in the bounded trial; raw requests/responses and visual facts are retained |
| State updates work | PASS | 23 verification events contained real unmatched effects or preconditions and produced updated symbolic states/problems |
| Replanning works | PASS | The trial invoked the planner 24 times, including after live visual discrepancies and an injected grasp failure |
| Active perception works / faithfully reconstructed | FAIL | Fixed-view released sim retained; Algorithm 2 control-flow component tested; VLM/motion/observation integration remains pending |
| Full trial finishes | PASS execution; task outcome FAIL | Seed 0 completed cleanly after 37 actions in 268.5 s. Released result: 0 success / 1 failed; the failure is preserved |
| Video/logging works | PASS | Full episode has raw provider requests/responses, state/action events, 59-frame first-person MP4 and 59-frame third-person MP4 |

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
- Completed Gemini end-to-end trial:
  `results/original/debug_episode/20260915T234514360281Z/run_metadata.json`;
  raw events are in the sibling `trace/events.jsonl`.
- Eighteen compatibility, transport, geometry and paper-control-flow tests pass.

## Remaining acceptance sequence

1. Diagnose the completed seed-0 task failure separately from pipeline execution:
   repeated room-valid pose sampling and second-bottle recovery consumed 37
   actions; retain released stochastic behavior and do not tune against this seed.
2. Validate the general paper algorithm separately from the fixed-view release:
   five paraphrases, majority vote, sufficiency, VLM direction, actual new sensor
   observation, symbolic correction and replan. Do not label the dormant generic
   preset-view wrapper as Algorithm 2. Record unspecified parameters explicitly.
3. Run 3–5 complete trials with the released failure injection probabilities;
   retain all seeds/outcomes, capture actual state, raw visual queries and videos.
4. Use only the released injection mechanism if additional exercise is needed;
   no engineered failures. The seed-0 trial already supplies a real
   situation-handling trace.
5. Update this report with pilot evidence and commit the passing baseline before any
   connector implementation.

## Checkpoint interpretation

The missing Ihlen file no longer blocks selection of an alternative released
task. Native material-system initialization is fixed by freeing the user inotify watch quota.
Camera/reset and Fetch lookat compatibility are fixed. The floor navigation
sampler now uses actual AABB side faces. Eight-action scripted execution and
videos work. A full Gemini-backed trial now demonstrates live predicate checks,
symbolic correction and replanning after real discrepancies. It completed but
failed the released task score after 37 actions; no success-rate conclusion is
supported by one seed. No 3–5-trial pilot is claimed. Eighteen unit tests pass.

Final native cleanup checks: no probe simulator processes remain. All
new probes reported zero changed files in monitored external NVIDIA/Omniverse
paths. No driver, system CUDA or other project was modified. Optional native
diagnostic interpreter/thread changes did not resolve startup. Process affinity
is the validated default on this machine; see `startup_affinity_fix.md`.
