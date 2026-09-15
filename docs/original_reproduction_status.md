# Original reproduction status

Last updated 2026-09-15. **Stage A is not yet reproduced.** No connector code
may be started from this checkpoint.

## Completed verification

- Clean official clone, dedicated branch, pinned upstream SHA.
- Source audit of simulation, real-robot wrappers, planner/validator integration,
  scene graph code, paper and prompt appendix.
- Dedicated Conda prefix with Python 3.10.20 and pddl 0.4.2 (see actual export
  for authoritative versions). No reuse of base or an existing research environment.
- Fast Downward and VAL built from the vendored sources without source changes.
- `scripts/planner_smoke.py` passes on unmodified `store_firewood` PDDL using
  the released `pddlsim` wrapper: eight plan actions, nine intermediate states,
  parsed grounded preconditions/effects, both symbolic goals satisfied, VAL valid.
- A second smoke run after clearing inherited ROS PYTHONPATH also passes.

Example artifact directory:
`results/original/planner_smoke/20260915T165500157887Z/`.
It contains `pddl_output.txt`, `val.txt`, `summary.json`, `wrapper_stdout.txt`.
These are symbolic planning artifacts, not debug-episode artifacts.

The original plan collects stick 3, places it on the table, collects stick 2,
and places it on the table. Each object transfer uses find/grasp/find/placeon.
The unused third grasp parameter grounds to the agent; this is allowed by the
released domain and is not evidence of a robot grasp implementation.

## Gates still required

| Gate | Status |
| --- | --- |
| Historical engine/source available | Pinned official OG 1.0.0 image located; engine archive downloading |
| Exact native torch/CUDA compatibility | Pending acquired engine metadata |
| Dataset download permission | User approved 22.32 GB bundle, conditional on compatibility and disk checks |
| Asset installation, task membership | Pending engine/archive checks; not downloaded |
| OpenAI credential, exact-model API call | OPENAI_API_KEY absent at audit; no API test |
| OmniGibson launch and camera | Not attempted |
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

## Pending compatibility fixes before simulation launch

1. Avoid `eval.py`'s eager optional Gemini import / Vertex constructor side effect.
2. Parameterize seed, trial count, output path and the existing baseline flags;
   use classical planning + both checks + predicate queries for the requested baseline.
3. Replace recursive output deletion with unique run directories.
4. Fail visibly on VLM transport/API failure instead of manufacturing affirmative
   predicate answers; retain exact prompt, endpoint and successful response semantics.
5. Validate Fetch observation shape, sensor modalities, object-instance mapping,
   BDDL activity names and object aliases against the pinned OG candidate.
6. Capture raw inputs/outputs, simulator state and VLM query events with explicit
   provenance. Preserve injection probabilities and released verification order.

The attachment ends mid-sentence in Section 26. Remaining instructions were
requested and are pending; do not infer omitted evaluation requirements.
