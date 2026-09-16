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

The next debug attempt reached the first Gemini request but the isolated Conda
OpenSSL configuration could not locate a certificate issuer. The runtime now
sets `SSL_CERT_FILE` to Ubuntu's existing read-only CA bundle at
`/etc/ssl/certs/ca-certificates.crt`. Certificate verification remains enabled;
no certificate or system package was added or changed. That second failed
attempt is likewise retained and excluded.

The CA-corrected attempt then completed 120 genuine Gemini responses against
121 recorded image requests before its manual debug bound. Pixel auditing ties
every request to the corresponding native sensor image. The trace includes
parsed votes and verifications, three executed camera motions, symbolic
corrections after failed insertion, and replanning. It also revealed a genuine
non-metric behavior: Gemini repeatedly reported left-side clearance in the
`LEFT_CONSTRAINED` condition, so the policy retained the incompatible left grasp
and retried insertion. This is an observed model/policy outcome, not an
infrastructure failure or a scientific trial.

Commit `d32ec05` corrects the live harness so bounded debug episodes are accepted
by their stated plumbing gates even if the task does not terminate. Each debug
episode must have byte-verified native image payloads, successful live Gemini
responses, parsed votes, and parsed verification. Across the pair, the runner
also requires a real camera motion, symbolic correction, and replanning. These
checks remain separate from scientific acceptance: a scientific attempt is
accepted only after a normal episode end without an infrastructure error.

## Post-freeze attached-object motion fix

The first `episode_000` attempt was stopped and excluded after five identical
`return_connector` failures. The trace isolated the cause: the custom connector
uses a native fixed joint, while the generic active-perception adapter's
compatibility path also translated `obj_held` during a base move. The duplicate
translation displaced the connector and destabilized the robot pose, leaving an
unreachable return target. Commit `a87360b` keeps that compatibility variable
unset in this custom task, restores the fixed workstation pose and orientation
before return, and adds a native regression mode. It does not alter prompts,
VLM answers, PDDL, action selection, task geometry, metrics, or any file under
`vlm-tamp`.

The exact committed regression performs native left grasp, a 0.25 m active camera
move, return, and release. It passed in 36.65 seconds with no remaining process;
`release_complete` reported success and the connector returned to
`[0.4300000072, 0.0000000013, 0.8349999785]`. The interrupted live attempt remains
preserved as infrastructure/debug evidence and will be retried from its frozen
seed; it is not a selected scientific result.
