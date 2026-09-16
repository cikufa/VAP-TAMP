# FROZEN CONNECTOR BENCHMARK

Implementation commit: **`5845d2a8459b14c8a6ec09d99ef96b4d2d22d93e`**.
Baseline commit: **`c31572043f7e1979033d2972e0e7e56f587a00f7`**.
Physical acceptance checkpoint: `01d348a`.

This document and `experiments/connector_handoff/freeze_manifest.json` form the
release record on top of that complete implementation. The implementation SHA
identifies every executable task input; the subsequent release-record commit
adds these documents and hashes without changing executable behavior. The exact
release-record commit can be obtained with:

```bash
git log -1 --format=%H -- experiments/connector_handoff/freeze_manifest.json
```

All 28 acceptance gates passed before freeze; 41 tests passed. No scientific
connector trial or live connector API call was run. Mock episodes are explicitly
NON-SCIENTIFIC MOCK VLM RUN. There is no scientific conclusion about the gap yet.

## Frozen inputs

- Physical dimensions, object poses, initial camera, two grasps, insertion path,
  collision checks and tolerances: [BENCHMARK_SPEC](../experiments/connector_handoff/BENCHMARK_SPEC.md).
- PDDL actions and nominal state: [domain](../experiments/connector_handoff/pddl/domain.pddl),
  [problem](../experiments/connector_handoff/pddl/problem.pddl),
  [model rationale](connector_pddl_model.md).
- Two debug seeds and 20 balanced evaluation seeds:
  [seed list](../experiments/connector_handoff/eval_seeds.json).
- Timing, first-handoff/recovery metrics, regret and counterfactual rules:
  [metrics](connector_metrics.md).
- Source hashes and acceptance measurements:
  [manifest](../experiments/connector_handoff/freeze_manifest.json).

The live launcher checks hashes before execution. Do not alter geometry, camera
pose, PDDL, grasp transforms, insertion tolerances, action ordering, view candidates,
or metric definitions after viewing live outcomes. A genuine software bug requires
an explicit new documented revision and rerunning affected trials into a new result
root; do not merge results from different revisions. No benchmark tuning is allowed
based on performance.

The inherited Gemini provider/model and reconstructed Algorithm 2 limitations
remain documented. This is a custom benchmark on the accepted reproduction,
not an exact artifact-level replication of the original paper.

## Post-freeze relocation fix

On 2026-09-16, the first live debug launch failed before OmniGibson startup
because the repository had moved from `/home/shekoufeh/VAP_TAMP` to
`/home/shekoufeh/seq-manip/VAP_TAMP`, while Conda's editable-install metadata
still contained the old absolute path. Commit `5845d2a` makes the isolated
runtime prepend its current project-local `.runtime/OmniGibson` checkout to
`PYTHONPATH`. This changes no scene, seed, PDDL, camera, action, metric, VLM,
or decision logic. The failed attempt remains preserved as infrastructure-only
evidence and is excluded from scientific results.
