# Active-perception release audit

Scope: static call tracing at upstream `39a52b0e10427ce91ddf3c1a177d3f4f782a61c3`,
with original planner execution checked separately. This audit predates the live
episodes; current evidence is in `baseline_acceptance_report.md` and
`paper_adapter_episode_results.md`. Sources are the pinned clone and [paper](https://arxiv.org/html/2604.26988v1)
(Algorithms 1–2, IV-B/C, V-B, appendix).

## Main finding: Case A

Section V-B explicitly limits simulation to predicate verification with a view
fixed relative to the base. The full viewpoint-selection algorithm is therefore
not demonstrated by the paper's simulation evaluation. Reproduce that experiment
first. A later moving-view simulation is a separate adaptation, not released
simulation or evidence that an integration was omitted from those experiments.

## Answers to the 13 release questions

| Question | Executable call-path evidence / answer |
| --- | --- |
| 1. Does simulation invoke active viewpoint movement? | `eval.py:108–109` sets module to None and `USE_ACTIVE_PERCEPTION=False`; `initialize_active_perception:121` is never called by the main loop. No uncertainty-driven sim movement. |
| 2. Only fixed-view verification? | Verification takes Fetch RGB at `check_states_and_update_problem:916`. Ordinary `goto:404` moves the base and calls `lookat:385`, which changes camera joints; `place_with_predicate:714` also calls lookat. Thus code is not literally motionless relative to base, but these are action-associated observations, not active verification views. |
| 3. Is real-robot AP complete? | No single inspected path implements all of Algorithm 2. `eval_real_robot.RealRobotPDDLExecutor.verify_predicate:275` connects uncertainty to head/base exploration. Separate `DKPrompt`/`VLMViewGuide` code performs task-specific wrist/front-camera reasoning. Neither is a complete generic five-paraphrase algorithm. |
| 4. Does AP feed state verification? | Yes in the real executor: `verify_predicate` returns the replacement answer; `check_states_and_update_problem:1065` can update PDDL. The optional hook in sim `eval.py:972` likewise replaces answers, but points to a real robot, not OmniGibson. |
| 5. Paraphrases/voting? | No five-question semantic voting in `GPT4VAgent.ask`, `GeminiAPIAgent.ask`, `ActivePerceptionModule`, or real executor. Semicolon batching is multiple predicates, not votes. DKPrompt repeats task-specific checks across views, which is different. Appendix specifies N=5. |
| 6. View sufficiency? | Absent in generic sim/ActivePerceptionModule loop. `VLMViewGuide.assess_grasp_information` and `assess_door_status` have sufficiency fields in task-specific prompts. |
| 7. VLM-guided directions? | Absent in generic ActivePerceptionModule. Present in separate VLMViewGuide movement-suggestion and DKPrompt lemon/door handlers. Grasp sufficiency prompt currently restricts its first choice to `front_side` or `sufficient`, despite broader docstrings. |
| 8. Geometric sampling? | Generic module samples eight positions on a circle about a detected instance with default radius 1 m, in fixed angular order. No VLM direction score. |
| 9. Motion used? | Generic module tries six preset head pan/tilt pairs, then base goals. Separate manipulation code calls UR5e arm and base routines for wrist/front-camera viewpoints. |
| 10. Budget? | Generic default is six head poses PLUS up to three base attempts, not three total viewpoints; returns add motion. DKPrompt lemon-halving uses four assessments, plate check two, fallen-half search three, door check three. Paper K and agreement threshold are not numerically fixed; N=5 is fixed in appendix. |
| 11. Camera? | Simulation: `fetch:eyes_Camera_sensor`, third-person viewer for logging. Generic module: robot observation RGB. VLMViewGuide: ROS `/usb_cam/image_raw` default, `/camera/color/image_raw` for front/door. Paper real hardware: wrist RGB-D. |
| 12. Updated state? | Simulation updates string facts using mismatches, writes `updated_problem.pddl`, reruns planner. Generic AP returns answer/image/success; it does not itself regenerate the graph. Real executor updates selected action facts; expected effects are hand-coded rather than generally extracted. |
| 13. Scene graph refresh before replanning? | Simulation has PDDL fact updates, no point-cloud/scene-graph refresh. Generic AP uses a preloaded map for view targets and does not call `add_obs` or `SceneGraph.update` after motion. Standalone graph exporter exists, but is not part of this loop. |

## Wrapper is a stub

`eval_with_active_perception.py` imports and constructs `ActivePerceptionModule`
then prints readiness. Its required `--domain`, `--problem`, and `--api-key`
arguments are not used to execute a task or construct a VLM. It does not import
`eval`, load OmniGibson, call a planner, verify predicates, or run an episode.

## Additional fidelity risks

- Simulation prompt permits `skip`, but `is_uncertain_vlm_response` does not
  recognize it. Enabling the dormant hook would not repair that inconsistency.
- `get_current_observation` returns a black image when robot observations are
  absent. This is not evidence of real sensor acquisition.
- Head exploration restores the head before its caller captures the returned
  image; logged image and the image that produced the accepted answer can differ.
- Generic base exploration returns to the original pose without updating the
  scene graph from the accepted view.
- Real `check_states_and_update_problem` only visually checks effects when a
  motion reports success; unresolved uncertainty does not force replanning.
- `DKPrompt._verify_lemon_is_halved` assumes success after budget exhaustion.
  Door handling forces multiple observations for half-open status. Do not
  transfer either task-specific rule into the connector diagnostic.

## Ordering relevant to the handoff hypothesis

The released simulation checks `Pre(A1)` initially, then after each action
batches current effects with `Pre(next action)` (see `eval.py:1300–1333`). Thus
successor preconditions are explicitly considered at the handoff. It does not
by itself establish whether useful information is acquired before grasping.
Planner-wide action knowledge, initial observations, task-associated head moves,
and incidental visibility must all be measured rather than suppressed.

```text
UNEXECUTED TEMPLATE — source-derived order, not an episode log
Plan A1 -> A2 -> A3
verify Pre(A1)
execute A1
verify changes Eff(A1) together with Pre(A2)
if mismatch: update PDDL; replan; verify new first-action preconditions
otherwise execute A2
verify changes Eff(A2) together with Pre(A3)
...
```

The paper's general loop instead checks each current action after navigation
and verifies positive effects afterward. Its pseudocode has ambiguous nested
`continue` behavior on precondition failure and inclusive `k=0..K` budgeting;
these must be recorded if a reconstruction is later implemented.

## Reconstruction boundary

N=5, binary majority rule, sufficiency prompts and directional suggestions are
specified well enough to reconstruct their logic. Numerical agreement threshold,
K, metric motion per direction, invalid response treatment, and graph refresh
details still require class-D assumptions. No such reconstruction has yet been
implemented. The connector stage remains gated on a committed original episode.
