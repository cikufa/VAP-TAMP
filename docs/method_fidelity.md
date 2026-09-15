# Method fidelity ledger

Audit: 2026-09-15. Upstream `39a52b0e10427ce91ddf3c1a177d3f4f782a61c3`.
Paper: [arXiv v1](https://arxiv.org/html/2604.26988v1), including its prompt appendix.
The project page links this paper and demonstration video; no separate runnable
supplement was identified in its visible links.

Classes: A released and executable; B released requiring compatibility fixes;
C paper-described missing logic actually reimplemented; D assumptions required;
E unavailable/unreproduced. A does not imply paper-equivalence. There are no
fully validated class-C integrations yet. Algorithm 2 control flow exists with
unit tests; live VLM/motion integration remains pending.

## Latest execution compatibility changes

| Component | What we run | Fidelity class | Reason |
| --- | --- | --- | --- |
| Runtime scheduling | Same engine/Conda stack, process restricted to audited CPUs 16–31 | B | Five task startups pass; unrestricted runtime had intermittent corruption/stalls. Hardware root cause is not established |
| Fetch target-directed head motion | Existing lookat target converted to Fetch joint positions using actual kinematics | B | OG helper hard-codes Tiago joints; actual camera pointing and limits tested |
| Navigation bounding-box samples | Same random sampler, with center-to-face distance corrected to half of full extent | B | OG 1.0 uses full extent and cannot find room-valid poses for the large floor |
| Semantic label lookup | OG 1.0's semantic_class_id_to_name function | B | Released import refers to an unavailable constant |
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
| Environment | OmniGibson/BEHAVIOR, no version pins | Incomplete Python 3.9 / torch 1.12.1 env | Python 3.10 planner-only prefix; OG 1.0.0 candidate | D | Provisioning only | Historical native engine uses Python 3.10 |
| Original simulator | Five household tasks | Fetch / Ihlen / store_firewood default | Not launched | E | No | Engine, assets and credentials gate |
| Full predicate-based baseline config | Preconditions + effects | Both false, VLM planning true at HEAD | Intended: both true, classical planning, NL false | B | Flags parameterized; no episode yet | Upstream defaults select another strategy |
| Simulation VLM | Simulation endpoint not separately named | GPT4VAgent uses OpenAI gpt-4-turbo | Gemini Developer API, gemini-3.5-flash-lite free tier; same prompts, 256x256 PNG and semicolon parsing | D; image request passed, episode pending | Yes | Released model unavailable and OpenAI credit exhausted; explicit provider/model substitution |
| Real VLM | Gemini Vision family, no endpoint ID | Gemini 2.0 flash exp in real executor / VLMViewGuide; optional Vertex 1.0 Pro Vision; offline map planner now Gemini 2.5 Flash | Not run | D/E | No model change | Cannot infer which exact endpoint produced published trials |
| Credentials | Not method logic | Two embedded credential literals found | Environment-variable reads replace both | B | Yes | Never use embedded upstream credentials |
| Primitive execution | Parameterized motion library | Teleport base/object, set states, gravity toggles | No physics execution | E | No | Native release must be reproduced before changes |
| Ground truth boundary | Visually grounded verification | handempty/inhand/filled/inside from bookkeeping; instance segmentation used inview | Preserve for original baseline, log source explicitly | D, runtime E | No | Must not claim purely visual state estimation |
| Failure injection | Table II per-action outcomes | Bernoulli success and conditional drop | Source-audited, not sampled experimentally | A source / E execution | No | Values preserved |
| Verification ordering | Current preconditions, then positive effects | First preconditions, then effects + successor preconditions; state-difference effects include negation | Source-derived trace only | D, runtime E | No | Ordering differs from general pseudocode |
| Paraphrase voting | Five variants, majority | Not implemented in inspected execution loops | None | E; potential C | No | Do not count semicolon batches as voting |
| Active view simulation | Fixed relative-base view in V-B | AP off; real-robot optional hook; wrapper stub | None | E | No | Case A, not omitted moving-view simulation |
| Generic real AP | VLM-guided views | Six head poses + up to three circular base candidates | Not executed | D/E | No | Geometric exploration differs from Algorithm 2 |
| VLMViewGuide | Sufficiency and directions | Task-specific grasp/door guidance | Source audited | E runtime | No | Not generic predicate verifier |
| Graph construction | RGB-D instances/relations | Standalone exporter + Stretch SceneGraph | Not executed | E | No | Simulation does not call exporter |
| Graph maintenance | Observation and expected-effect updates | PDDL string corrections; no generic observation refresh in AP | Source audited | E runtime | No | Missing integration remains explicit |
| Connector / physical insertion | New diagnostic, not paper task | Not released | Not implemented | E | No | Successful original baseline commit required first |

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
  necessary, gemini-2.5-flash is a concrete candidate already present in upstream;
  it requires explicit approval and remains a scientific deviation.

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
