# VAP-TAMP implementation map

All release paths below are relative to this clone at upstream
`39a52b0e10427ce91ddf3c1a177d3f4f782a61c3`. Line numbers refer to upstream.
An identified function is not necessarily runnable or paper-equivalent.

## Planning and action knowledge

| Responsibility | File / class / function | Behavior |
| --- | --- | --- |
| PDDL parsing | `vlm-tamp/pddl_sim.py`, `pddlsim`, imported `pddl.parse_domain`, `parse_problem` | Domain action parsing; initial-state parsing uses text lines |
| FD invocation | `pddlsim.plan` | `python ./downward/fast-downward.py`, seq-opt-fdss-1, 10-second search |
| Problem generation/correction | `eval.py:update_states_by_fact:828`, `write_states_into_problem:849` | Correct contradicted facts in predicted state; write updated_problem.pddl |
| Predicted states and validation | `pddlsim.get_intermediate_states` | Run VAL `Validate -v`, interpret Adding/Deleting output |
| Replanning | `eval.py:1220` main while loop | On mismatch break current action loop and plan from updated file |
| Preconditions | `pddlsim.get_preconditions_by_action`, `reformat_fact_using_values` | Bind PDDL variables to plan arguments |
| Effects | `pddlsim.get_effects_by_states` | Diff consecutive VAL-predicted states, including negative changes |
| Natural language | `eval.py:translate_fact_to_question:804` | Template per recognized predicate; strips explicit negation for affirmative query |
| Action-level baseline prompts | `eval.py:check_states_and_update_problem`, CHECK_IN_NL | Alternate success/feasibility questions; should be false for predicate approach |
| VLM-generated plan baseline | `gpt4v.py:GPT4VAgent.plan` | Full problem/domain in prompt; writes pddl_output.txt |

## Perception and scene graphs

| Responsibility | Location | Boundary |
| --- | --- | --- |
| Simulation first person | `eval.py:get_fpv_rgb:307` | Fetch eyes camera RGB |
| Simulation third person | `eval.py:get_tpv_rgb:311`, `watch_robot:397` | Viewer camera; logging only |
| Semantic/instance segmentation | `eval.py:get_seg_semantic:315`, `get_seg_instance:319` | Simulator ground-truth render modalities |
| Visibility | `eval.py:inview:352` | Instance IDs mapped to scene objects; requires dataset/version-compatible ID semantics |
| Action-associated head direction | `eval.py:lookat:385` | Head joint goal uses ground-truth object pose |
| Real observations | `active_perception.py:get_current_observation` | HomeRobot/UR5e client RGB; black fallback on missing observation |
| Open-vocabulary detection | `stretch_ai/src/stretch/perception/wrapper.py:OvmmPerception`, `create_semantic_sensor` | Detic/other backends selected from parameters, not used by released sim |
| Voxel map | `stretch_ai/src/stretch/mapping/voxel/voxel.py:SparseVoxelMap.add_obs`, `add`, `read_from_pickle` | RGB-D observation aggregation and saved-map loading |
| Instances | `stretch_ai/src/stretch/mapping/instance/` | Instance memory and view crops |
| Scene graph construction | `generate_scene_graph.py:load_voxel_map_with_instances`, `extract_scene_graph`, `scene_graph_to_json` | Standalone export from saved voxel map |
| Graph relationships/update | `stretch_ai/src/stretch/mapping/scene_graph/scene_graph.py:SceneGraph.update`, `get_relationships`, `near`, `on`, `inside` | Geometric relations; not invoked on each generic AP observation |
| Simulation graph update | No such call in eval.py | Updates symbolic fact list instead |

## VLM

| Path | Model / prompt / responses |
| --- | --- |
| `gpt4v.py:GPT4VAgent._prepare_samples`, `_request_gpt4v`, `ask` | gpt-4-turbo, REST; resize RGB 256x256; prompts.txt requests yes/no/skip; semicolon split. No paraphrases or voting. Some HTTP failures fabricate affirmative strings—must surface as API failure before scientific runs. |
| `gemini.py:GeminiAgent` | Vertex gemini-1.0-pro-vision; cloud project hard-coded, constructor runs on module import; optional but eagerly imported by eval.py |
| `gemini_api.py:GeminiAPIAgent` | google.generativeai, gemini-2.0-flash-exp default; each question asks yes/no/uncertain; exceptions become uncertain |
| `VLMViewGuide.py:VLMViewGuide` | Direct Gemini REST; task-specific sufficiency, direction, door prompts; ROS image subscriptions |
| `stretch_ai/src/stretch/llms/multi_crop_gemini_client.py` | gemini-2.5-flash default for offline map planning, different pathway |
| `eval.py:is_uncertain_vlm_response:905` | Keyword matching; does not include release prompt's skip token |
| Repeated query logic | No generic N=5 routine found in traced release paths; task-specific repeated observations in DKPrompt are not semantic paraphrase voting |

## Active perception

`eval.py:initialize_active_perception` constructs the real-robot module if called;
the simulation main loop never calls it. `eval_with_active_perception.py:main`
only initializes that module and exits.

`active_perception.py:ActivePerceptionModule`:

- Trigger: uncertainty keywords in its caller's predicate answer.
- Target: `_extract_target_object`, usually first object argument; category-level
  name loses instance suffix, and then first matching detected instance is used.
- View representation: base `(x, y, theta)` on an eight-point 1 m circle.
- Suggestion: `_sample_viewpoints_around_object` geometry, not VLM guidance.
- Motion: `_try_head_camera_exploration` six head poses, then `navigate_to_goal`.
- Retry: `_is_confident_response`; one yes/no answer can terminate exploration.
- Budget: default three base attempts in addition to head moves.
- State feedback: returns answer/image/success; caller updates PDDL on mismatch.

`VLMViewGuide` and `DKPromptExecutor` provide separate sufficiency/direction
reasoning for manipulation and doors. DKPrompt uses ROS1 controllers, whereas
Stretch mapping/navigation includes ROS2 bridge code. Do not assemble pieces
from these paths and label them an unchanged released algorithm.

## Execution and simulation

| Primitive / setup | Location | Released implementation |
| --- | --- | --- |
| Config | `eval.py:1095–1127` | OG fetch_behavior.yaml, Ihlen_0_int, store_firewood, task-relevant objects, no ceilings, offline cached activity instance |
| Initialization | `eval.py:1140–1218` | Construct OG environment; reload per trial; Fetch; starter primitives; alias firewood objects to wooden_stick names |
| Navigation | `goto:404`, `sample_teleport_pose_near_object:201` | Sample collision-free base pose and teleport; head lookat; possible held-object drop |
| Grasp | `grasp:515` | Visibility/hand checks, stochastic failure; teleport object above robot and disable gravity; no grasp-specific in-hand transform |
| Placement | `place_with_predicate:714`, `place_on_floor:678` | Sample predicate placement, teleport, restore gravity, update bookkeeping |
| Open / close | `openit:621`, `closeit:636` | Set OG Open state with random failure |
| Cut | `cut_into_half:649` | Particle/object-state manipulation with random failure; inspect exact native behavior before adapting |
| Turn on / heat | `turnon:454` | Set native toggle state; symbolic heat/cook effects handled by task |
| Fill | `fill_sink:467`, `fill:574` | Set particle-system states; scripted placement/regrasp internally uses oracle=True |
| Time stepping | `run_sim:372` | Physics stepping plus third-person frame output |
| Failure injection | `eval.py:83–96`, primitive branches | Bernoulli success then 0.5 conditional drop where applicable |
| Ground truth visible to verifier | `GT_PREDS`, `check_gt_facts:864` | handempty, inhand, filled, inside; inhand check only tests any held object |
| Ground truth visible to primitives | `env.task.object_scope`, OG object states/poses, segmentation | Used to execute released simplified primitives and assess visibility |
| Trial scoring | Bottom of `eval.py` | Task-specific OG final-state checks; preserve distinction from symbolic goal success |
| Release logging | `check_states_and_update_problem` result dict and main plotting loop | FPV/TPV composites, questions/answers, mismatch booleans; not full raw-response/AP event logging |

## Local additions at this checkpoint

- `scripts/project_runtime.sh`: project-contained Conda/cache settings.
- `scripts/build_planners.sh`: native planner builds using existing build tools.
- `scripts/planner_smoke.py`: original wrapper, original domain/problem,
  unique output directory, explicit VAL verification and symbolic goal checks.
- Two credential assignments switched to environment lookup. No VLM endpoint,
  failure probability, PDDL domain, verification semantics, or motion primitive
  has been changed.

No connector, moving-view integration, video pipeline, or counterfactual replay
has been implemented. The original simulation success gate is still unmet.
