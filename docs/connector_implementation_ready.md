# Connector benchmark implementation ready

**FROZEN CONNECTOR BENCHMARK. All 28 acceptance gates pass; 41 tests pass.**
No live connector API request or scientific connector trial has been run. The
remaining step is the frozen live evaluation when credentials/quota are available.
Mock behavior establishes software integration only.

## Required implementation record

| # | Item | Result |
|---|---|---|
| 1 | Baseline SHA | `c31572043f7e1979033d2972e0e7e56f587a00f7`; accepted by explicit user instruction |
| 2 | Connector implementation SHA | `5845d2a8459b14c8a6ec09d99ef96b4d2d22d93e`; post-freeze relocation fix only; frozen scientific inputs remain unchanged |
| 3 | Files added | [Complete inventory](connector_file_inventory.md); task package, new assets/PDDL, validation, execution, metrics, replay and media scripts |
| 4 | Baseline files modified | **No `vlm-tamp/` source changed.** Historical `docs/method_fidelity.md` connector status updated; connector-specific docs added/updated |
| 5 | VAP-TAMP decision logic | **Unchanged.** Actual baseline AST loop and verification functions; task dispatch/visualization bindings only |
| 6 | Physical task | Native Fetch acquires a keyed connector from a feed nest and inserts it into a panel socket while held |
| 7 | Hidden variable | Identical mounting rib at Y=+0.100 m or −0.100 m; LEFT_CONSTRAINED/RIGHT_CONSTRAINED only in evaluation metadata |
| 8 | gL/gR | EEF offsets (0,+0.095,0)/(0,−0.095,0), roll π/2, yaw ∓π/2; distinct lateral wrist bulk, unchanged connector key orientation |
| 9 | Local grasp measurements | gL 10/10; gR 10/10 across both conditions. Approach, attachment, lift, pose and hold recorded per trial |
| 10 | Four-way compatibility | LEFT: gL 0/5, gR 5/5 INSERT; RIGHT: gL 5/5, gR 0/5 INSERT |
| 11 | Failure mechanism | Native wrist/finger overlap with `/World/fixture/base_link`, before target insertion depth; no condition/grasp success if-statement |
| 12 | Initial camera | Settled position approximately [0.22194704413414018, -0.0003845253959297905, 1.283115863800049]; 256×256 native RGB. Full rotation/joints in specification and observability JSON |
| 13 | Informative poses | Existing target-relative left/right 0.25 m moves. Useful geometry within two moves; all requested audit moves reached. Full per-move extrinsics saved |
| 14 | Observability | [2×4 native matrix](../results/custom_connector/benchmark_validation/observability/acceptance01/connector_observability_matrix.png); initial fixture pixels zero in both conditions; connector visible |
| 15 | PDDL actions | grasp_connector_left/right, insert_from_left/right_grasp, return_connector, find |
| 16 | Preconditions/effects | [PDDL rationale](connector_pddl_model.md) and [exact domain](../experiments/connector_handoff/pddl/domain.pddl); FD and VAL passed nominal and both corrected states |
| 17 | GRASP fairness | GRASP requires available, handempty, inview only; **no INSERT clearance or future-success precondition** |
| 18 | Ground-truth boundary | Same nominal problem in both conditions; no fixture side in planner/online object memory. Clearance comes from unchanged visual verification. Physical bookkeeping is task-local proprioception |
| 19 | Native mock integration | Straight: 2 actions, successful grasp/INSERT. Reactive: 4 actions, real AP/new RGB, correction, replan, return/regrasp/INSERT. 24/49 image payloads respectively verified pixel-for-pixel |
| 20 | Video/log pipeline | Both mock videos decode; contact sheets, timelines, raw RGB-D, request/response logs, symbolic diffs, sequential FD/VAL logs and four oracle videos exist |
| 21 | Evaluation seeds | [Frozen seed file](../experiments/connector_handoff/eval_seeds.json): 10 left, 10 right; two distinct non-metric debug seeds |
| 22 | Metrics | First-handoff Y1/Y2, final recovery success, timing, decision change, regret, costs and exclusive attribution implemented; mock/live mixing rejected |
| 23 | Counterfactual replay | Native exact saved-state alternate gR replay succeeded. This mock handoff was abandoned before INSERT; the replay is plumbing evidence, **not an avoidable physical failure claim** |
| 24 | Live command | Below; automatically runs two non-metric live debug episodes before the frozen 20 |
| 25 | Remaining blockers | No implementation acceptance blocker. Live quota/credentials and actual model behavior remain untested for this connector scene. Live results may support, weaken or falsify the hypothesis |

## Physics acceptance

| Fixture | gL local | gR local | INSERT after gL | INSERT after gR |
|---|---:|---:|---:|---:|
| LEFT_CONSTRAINED | 5/5 | 5/5 | 0/5 | 5/5 |
| RIGHT_CONSTRAINED | 5/5 | 5/5 | 5/5 | 0/5 |

These are deterministic-reset engineering measurements, not confidence estimates
for new assemblies. Successful insertion pose errors were 5.19–5.44 mm against an
8 mm tolerance. Native worker runs cleaned up with no monitored external runtime
path changes. Host driver, system CUDA/Vulkan/packages and GoFlow/Isaac were not changed.

## Baseline fidelity self-audit

| Question | Answer |
|---|---|
| Changed AP logic? | NO |
| Changed verification logic? | NO |
| Changed VLM voting? | NO |
| Changed planner/search/cost? | NO |
| Changed replanning or recovery policy? | NO |
| Added successor lookahead? | NO |
| Added competence prediction? | NO |
| Added NBV objective? | NO |
| Manually triggered online inspection? | NO |
| Added new physical scene? | YES |
| Added task-specific PDDL? | YES |
| Added legitimate physical primitives? | YES |
| Added two locally successful grasp configurations? | YES |
| Created hidden successor geometry? | YES |
| Added successor constraints to GRASP? | NO |
| Exposed obstruction side to planner? | NO |

The single-literal PDDL parser compatibility wrapper normalizes syntax, preserving
exact applicability and released fact formatting. Task-local vocabulary binds
five physical questions per new visual predicate in a private instance of the
unchanged verifier. The original eval loop retains effects-plus-next-preconditions
ordering, nominal FD tie-breaking, K=2, 4/5 agreement, direction prompts, motion
implementation, correction and replanning. No learned model is trained:
[training statement](connector_training_statement.md).

## Commands

From the repository root, with the existing key exported in the calling shell:

```bash
.runtime/envs/vaptamp-repro/bin/python scripts/run_connector_vaptamp.py \
  --seeds experiments/connector_handoff/eval_seeds.json --live-vlm
```

The launcher uses the existing isolated engine environment. It checks frozen
hashes, pins the accepted Gemini backend/model, runs two non-metric debug episodes,
then the 20 seeds. Completed task failures are retained. API/infrastructure failures
stop the run and preserve the attempt; the same command resumes in a new attempt.
No mock fallback exists. Debug images and parsing are checked; AP is not forced
if the real model does not request it. Native AP mechanics are already validated
by the mock path.

One-command analysis, including missing offline counterfactuals:

```bash
.runtime/envs/vaptamp-repro/bin/python scripts/summarize_connector_results.py \
  --input results/custom_connector/live_trials
```

It generates metrics, counterfactual results, videos/contact sheets/timelines and
an aggregate report, excluding the debug directory. Use `--no-replay` only for a
provisional analysis that explicitly reports missing counterfactuals.

Read-only gate check:

```bash
.runtime/envs/vaptamp-repro/bin/python scripts/validate_connector_acceptance.py
```

## Review artifacts

- [Physics CSV](../results/custom_connector/physics_validation.csv)
- [Four-way physics videos](../results/custom_connector/benchmark_validation/physics/acceptance01)
- [Observability matrix](../results/custom_connector/benchmark_validation/observability/acceptance01/connector_observability_matrix.png)
- [Straight mock video](../results/custom_connector/mock_validation/acceptance01/trial_logs/straight/episode/episode.mp4)
- [Reactive mock video](../results/custom_connector/mock_validation/acceptance01/trial_logs/replan/episode/episode.mp4)
- [Reactive contact sheet](../results/custom_connector/mock_validation/acceptance01/trial_logs/replan/episode/episode_contact_sheet.png)
- [Reactive timeline](../results/custom_connector/mock_validation/acceptance01/trial_logs/replan/episode/episode_timeline.png)
- [Mock-only analysis report](../results/custom_connector/mock_validation/acceptance01/report.md)
- [Machine-readable acceptance gates](../results/custom_connector/acceptance_audit.json)

Artifacts stay in this workspace's ignored results directory; source, seeds,
specification and the hash/evidence manifest are committed. No remote push.

## Scientific limits and interpretation

Original paper, public release and this reconstruction are distinct. The public
simulation release lacked the complete moving-view Algorithm 2 implementation.
The accepted baseline reconstructs that adapter and carries documented OG/Fetch
compatibility assumptions, cached Wainscott bringing_water scene substitution,
and Gemini `gemini-3.5-flash-lite` substitution for the simulation OpenAI backend.
Its earlier live AP episode ended on daily quota. The user explicitly accepted
`c315720` as the frozen basis for this new connector benchmark; that does not make
the earlier paper reproduction exact or complete.

The connector scene and physical skills are new, deterministic task abstractions;
they do not reproduce the released household skills' synthetic failure injection.
See [full provenance](connector_experiment_provenance.md) and the historical
[method-fidelity ledger](method_fidelity.md). No successor-aware method was added.
The mock reactive trajectory is intentionally a software test and cannot establish
a reactive gap. Only the later frozen live results, with counterfactuals and confound
review, can yield GAP FALSIFIED AT THIS LEVEL, PARTIAL GAP, HYPOTHESIZED REACTIVE
GAP OBSERVED, or INCONCLUSIVE.
