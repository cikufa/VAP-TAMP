# Method fidelity ledger

Updated: 2026-09-16. Upstream `39a52b0e10427ce91ddf3c1a177d3f4f782a61c3`.
Paper: [arXiv v1](https://arxiv.org/html/2604.26988v1), including its prompt appendix.
The project page links this paper and demonstration video; no separate runnable
supplement was identified in its visible links.

Classes: A released and executable; B released requiring compatibility fixes;
C paper-described missing logic actually reimplemented; D assumptions required;
E unavailable/unreproduced. A does not imply paper-equivalence. The fixed-view pilot now has five completed trials in two conditions. An optional
Algorithm 2 adapter has live voting, five executed view changes, new observations,
state correction and continued planning. Its full episode hit daily API quota;
see `paper_adapter_episode_results.md` for the incomplete-trial boundary.

## Latest execution compatibility changes

| Component | What we run | Fidelity class | Reason |
| --- | --- | --- | --- |
| Runtime scheduling | Same engine/Conda stack, process restricted to audited CPUs 16–31 | B | Five task startups pass; unrestricted runtime had intermittent corruption/stalls. Hardware root cause is not established |
| Fetch target-directed head motion | Existing lookat target converted to Fetch joint positions using actual kinematics | B | OG helper hard-codes Tiago joints; actual camera pointing and limits tested |
| Navigation bounding-box samples | Same random sampler, with center-to-face distance corrected to half of full extent | B | OG 1.0 uses full extent and cannot find room-valid poses for the large floor |
| Semantic label lookup | OG 1.0's semantic_class_id_to_name function | B | Released import refers to an unavailable constant |
| Movable-object room lookup | Current segmentation-map room, fixed-object annotated rooms retained | B | Cached in_rooms remains stale after transport; native regression validated |
| Base-copy self filtering | Restore simplified-base-copy filtering on Fetch's original-copy fallback | B/D | Native torso/elbow self-overlap otherwise blocked all tested AP directions |
| Optional AP ground tolerance | Existing base/wheel lawn contacts allowed only when a 1 cm raised-copy check clears | D | Measured shallow support overlap; separately validated, not a paper parameter |
| Execution diagnostics | Source-extracted primitive replay without a VLM; videos and physical-state logs | Diagnostic only | Not counted as a VAP-TAMP trial; failed grasp and false task result preserved |

Failure probabilities, fixed-view navigation behavior (`tuck` after `lookat`),
PDDL and verification order remain unchanged. Geometry changes affect
sampled poses and must be disclosed; they are not an exact-byte reproduction of
the broken helper. Full baseline acceptance remains incomplete.

| Component | Paper | Official repo | What we run | Fidelity class | Modified? | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| Fast Downward | Classical PDDL planning | Vendored source; `seq-opt-fdss-1`, 10 s search | Built source; original firewood wrapper smoke | A | No algorithm change | Eight actions, validated |
| VAL | Classical state/action reasoning | Vendored source; verbose state replay | Built CMake Release; nine states for eight actions | B (build setup) | Build script only | README omits initial CMake configure |
| PDDL parser | Action knowledge extraction | `pddl` package missing from env file | pddl 0.4.2; all original plan preconditions extracted | B | Dependency added | API checked by wrapper smoke |
| Environment | OmniGibson/BEHAVIOR, no version pins | Incomplete Python 3.9 / torch 1.12.1 env | Dedicated Python 3.10.21, OG 1.0, torch 2.0.1/cu118, Isaac 2023.1.1 | D | Project-local provisioning | Native stack validated; host driver unchanged |
| Original simulator | Five household tasks | Fetch / Ihlen / store_firewood default | OG 1.0, Isaac 2023.1.1, Fetch; cached Wainscott bringing_water | D scene substitution | Compatibility fixes | Five new trials completed; missing exact Ihlen artifact remains |
| Full predicate-based baseline config | Preconditions + effects | Both false, VLM planning true at HEAD | Both true, classical planning, NL false | B | Parameterized flags | Completed five recorded trials |
| Simulation VLM | Simulation endpoint not separately named | GPT4VAgent uses OpenAI gpt-4-turbo | Gemini Developer API, gemini-3.5-flash-lite free tier; same prompts, 256x256 PNG and semicolon parsing | D; bounded episode completed | Yes | Released model unavailable and OpenAI credit exhausted; explicit provider/model substitution |
| Real VLM | Gemini Vision family, no endpoint ID | Gemini 2.0 flash exp in real executor / VLMViewGuide; optional Vertex 1.0 Pro Vision; offline map planner now Gemini 2.5 Flash | Not run | D/E | No model change | Cannot infer which exact endpoint produced published trials |
| Credentials | Not method logic | Two embedded credential literals found | Environment-variable reads replace both | B | Yes | Never use embedded upstream credentials |
| Primitive execution | Parameterized motion library | Teleport base/object, set states, gravity toggles | Native execution with released stochastic failures | B/D | Geometry/room compatibility repairs | No physical grasp-planner equivalence claimed |
| Ground truth boundary | Visually grounded verification | handempty/inhand/filled/inside from bookkeeping; instance segmentation used inview | Preserved and recorded in live verification traces | D | Diagnostic final predicates added, not fed to planner | Not purely visual state estimation |
| Failure injection | Table II per-action outcomes | Bernoulli success and conditional drop | Active in all fixed-view trials | A | No probability changes | Failures, discrepancies and recovery retained |
| Verification ordering | Current preconditions, then positive effects | First preconditions, then effects + successor preconditions; state-difference effects include negation | Same released order in live traces | D | No | General Algorithm 1 ordering difference remains explicit |
| Paraphrase voting | Five variants, majority | Not implemented in inspected execution loops | Optional paper adapter; five separate same-image queries | C/D | Separate mode | Not mixed with fixed-view pilot; Gemini enum formatting is an adaptation |
| Active view simulation | Fixed relative-base view in V-B | AP off; real-robot optional hook; wrapper stub | Fixed-view default retained; optional native Algorithm 2 adapter executed five real view changes | C/D optional | Opt-in only | Not an exact reproduction of V-B; full AP episode incomplete on daily quota |
| Generic real AP | VLM-guided views | Six head poses + up to three circular base candidates | Not executed | D/E | No | Geometric exploration differs from Algorithm 2 |
| VLMViewGuide | Sufficiency and directions | Task-specific grasp/door guidance | Source audited | E runtime | No | Not generic predicate verifier |
| Graph construction | RGB-D instances/relations | Standalone exporter + Stretch SceneGraph | Not executed | E | No | Simulation does not call exporter |
| Graph maintenance | Observation and expected-effect updates | PDDL string corrections; no generic observation refresh in AP | Live PDDL corrections; optional RGB-D instance memory + symbolic facts | C/D optional | Separate adapter | Small task-object memory, not complete voxel-map reconstruction |
| Connector / physical insertion | New diagnostic, not paper task | Not released | Native crossover and mock pipeline validated; see connector_implementation_ready.md | D, custom benchmark | New task files only | User accepted c315720 as frozen baseline; no live connector scientific results |

The fixed-view pilot is execution evidence, not model equivalence. Two of three
trials after the room fix physically achieved the released PDDL goal; all historical
height-based scores were false. See `bringing_water_pilot_results.md` and
`bringing_water_goal_scoring.md`. No population success-rate comparison is claimed.

## Failure probabilities

These are conditional on reaching the injection branch. Visibility, sampling,
and other primitive precondition failures are additional outcomes.

| Action | Paper outcomes | Code calculation |
| --- | --- | --- |
| Navigation/find | held-object drop 0.10; visibility/free-space failures not assigned fixed probabilities | `(1 - NAV_SUCCESS_PROB=0.8) * 0.5 = 0.10` drop if holding |
| Grasp | unchanged 0.25, drop 0.25 | `(1 - PICK_SUCCESS_PROB=0.5)`, split equally |
| Placein/placeon | remain held 0.10, drop 0.10 | `(1 - PLACE_SUCCESS_PROB=0.8)`, split equally |
| Fill | not filled 0.05, drop 0.05 | `(1 - OTHER_ACTION_SUCCESS_PROB=0.9)`, split equally |
| Open/close/turnon | unchanged 0.10 | individual success constants 0.9 |
| Cut | unchanged 0.25, knife drop 0.25 | `(1 - HALVE_SUCCESS_PROB=0.5)`, split equally |
| Place on floor | Not separately listed | success 0.8; must retain released branch behavior |

The navigation success constant 0.8 does not imply a 20% drop rate. The code's
two-stage random draw agrees with the paper's 10% held-object-drop entry.

## VLM availability and endpoint provenance

- `vlm-tamp/gpt4v.py` retains the released prompt preparation and parsing;
  `vlm-tamp/vlm_backends.py` supplies modular Gemini and OpenAI transports.
  The active substitution is Gemini 3.5 Flash-Lite with 256x256 input and 50 output
  tokens for verification. See `gemini_backend_substitution.md`.
- `vlm-tamp/gemini.py`: Vertex `gemini-1.0-pro-vision`, hard-coded cloud project,
  and constructor invoked at module import even when GPT is selected. Remove
  this optional import side effect before the GPT baseline, rather than requiring
  unrelated Google credentials. The unused eager import has now been removed from eval.py.
- [Google lifecycle](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions)
  lists `gemini-1.0-pro-vision-001` retirement on 2025-04-21.
- `gemini_api.py` and `VLMViewGuide.py` default to `gemini-2.0-flash-exp`.
  The [Gemini deprecation page](https://ai.google.dev/gemini-api/docs/deprecations)
  lists stable Gemini 2.0 retirement on 2026-06-01, but does not certify the
  specific experimental alias's availability. No authenticated alias probe ran.
- `stretch_ai/src/stretch/llms/multi_crop_gemini_client.py` now defaults to
  gemini-2.5-flash. This offline mapping path does not authorize switching the
  simulation or historical active-perception model. If a substitute becomes
  necessary, the old Gemini 2.5 alias was already present upstream. Its availability and
  past model-choice discussion are historical; the explicitly authorized active
  substitution is Gemini 3.5 Flash-Lite, documented separately.

## Interpretation limits

No task success estimate, failure rate, counterfactual benefit, or conclusion
about prospective information acquisition is supported by this audit alone.
In particular, original symbolic planning success cannot certify physics,
camera visibility, insertion clearance, VLM behavior, or active perception.

## Original task scoring discrepancy

Pinned BDDL 3.5.0 `store_firewood/problem0.bddl` requires all three firewood
objects on the table. The released PDDL problem contains goals for sticks 2
and 3 only; released trial scoring checks their heights above 0.3 m and that
neither is held. These are distinct criteria. Preserve released behavior,
and report both released scoring and actual task predicates when episodes run.
