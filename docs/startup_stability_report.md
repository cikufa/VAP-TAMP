# Sequential startup characterization

Five clean, sequential process launches on 2026-09-15. All used the pinned
OG/engine and contained runtime settings, with bringing_water selected for
scene loading after engine initialization. **0/5 passed.**

| Probe | Launch UTC | Wall seconds incl. cleanup | Whole-GPU MiB before → after | Result | Remaining simulator processes |
| --- | --- | ---: | --- | --- | ---: |
| 1 | 2026-09-15T17:41:30.741055+00:00 | 129.0 | 1673 → 1743 | FAIL, timeout | 0 |
| 2 | 2026-09-15T17:43:39.872114+00:00 | 129.1 | 1743 → 1481 | FAIL, timeout | 0 |
| 3 | 2026-09-15T17:45:49.104704+00:00 | 128.5 | 1481 → 4686 | FAIL, timeout | 0 |
| 4 | 2026-09-15T17:47:57.641394+00:00 | 128.4 | 4686 → 8675 | FAIL, timeout | 0 |
| 5 | 2026-09-15T17:50:06.083594+00:00 | 128.4 | 8675 → 8670 | FAIL, timeout | 0 |

For all five, engine initialization did not complete within 120 s. Scene-load
duration is null/not reached, not zero. Each run records start and initialization
phase timestamps in its `phases.jsonl`, 2 s GPU samples, exit code, terminal log,
Kit log, timeout and cleanup status in `summary.json`.

All five Python traces stop in `omni.usd.add_hydra_engine`, called from the
viewport's stage-opened handler during `SimulationApp.create_new_stage`.
No VAP-TAMP planner, predicate query, or action executed. There is no logged
shader-compilation completion establishing a first-launch warmup explanation.
Repeatedly exceeding the timeout is not characterized as normal warmup.
A native debugger investigation follows this series.

SIGTERM was given a five-second grace period, followed by SIGKILL when needed.
No child process group or simulator process remained after each cleanup.
The baseline does not pass graceful startup/shutdown: killed processes are
recorded as failures, not successful shutdowns.

Whole-GPU memory rose during later probes because an unrelated GoFlow process
started concurrently (recorded in `gpu_attribution.json`). It was not stopped or
modified. These total-memory values cannot establish a leak trend attributable
to OmniGibson. Live attribution showed the probe at 456 MiB and GoFlow at
6924 MiB at 17:50:45 UTC. Later harness revisions record process-level GPU
attribution before and after each probe. No stale probe process persisted.

Monitored external NVIDIA/Omniverse cache, data, Documents and log trees had
zero changed files in all five comparisons. This is scoped filesystem metadata
monitoring, not a claim that every filesystem write was syscall-traced. All
configured logs, caches and data paths stay project-local. No drivers, system
CUDA, sysctl limits, or other applications were modified.

Artifacts:
`results/original/startup/20260915T174130727503Z/`.
Each `probe_N.log` is the last terminal log; `probe_N/kit.log` is its native log.

## Native debugger and follow-up

A sole-process gdb launch was interrupted after 75 s to collect all native
thread stacks. The main thread waits in `libcarb.tasking.plugin.so`, called
from `librtx.neuraylib.plugin.so` and the RTX scene renderer. This locates the
wait in material-system initialization; it does not establish the root cause.
Gdb exit 0 means successful trace collection, not successful simulator startup.
No inferior process remained. Artifact:
`results/original/startup_debug/20260915T175214589413Z/gdb.log`.

A process-local OMP_NUM_THREADS=1 test also timed out at 120 s; the setting
was not adopted. Artifact: `results/original/startup/20260915T175437134536Z/`.

The native material-backend extension's own test configuration sets timeout
1000 s and comments that RTX warmup can sometimes take about 800 s. Therefore
120 s timeouts cannot alone establish a permanent deadlock. A single fresh-cache
probe was allowed 900 s in
`results/original/startup/20260915T175652016448Z/`.
Old caches were retained. This separates bounded timeout evidence from a claim
that normal initial compilation is impossible.

A 15 s /proc thread-activity sample during this longer wait shows no busy
compiler thread; the highest observed thread CPU use was 0.08 s (CUDA event
handler), with other threads mostly sleeping or waiting. This is evidence
against active CPU compilation during that interval, not proof of deadlock.

A reported MDL deadlock in newer Isaac Sim versions involves asynchronous
rendering, but the pinned OG kit explicitly sets asyncRendering and
asyncRenderingLowLatency false. That workaround does not directly match this
configuration and was not blindly applied. An optional diagnostic can separately
turn off synchronous asset-load flags; it is not enabled in the baseline launcher.

The native validation log also warns about IOMMU. This warning was present with
prior successful starts and is not sufficient to attribute the current wait to
IOMMU. No BIOS, kernel, driver or system CUDA changes were made.

The fresh-cache run also timed out after 900 s without engine readiness or
scene loading. It was terminated and reaped; no simulator processes remained
and monitored external files were unchanged. Thus this run did not recover
within the engine test's stated long warmup window. It still does not prove
which library or configuration causes the wait.

Next diagnostic: preload Torch/TorchVision before engine launch, matching the
released evaluator's import order. The earlier probes let Kit load its bundled
Torch during extension startup. Versions are compatible, and the bundled and
Conda libgomp files have identical SHA256; this is an import-order test, not a
claim of a proven binary mismatch.

The evaluator-order preload probe also timed out at 120 s:
`results/original/startup/20260915T181200413759Z/`. Its phase log confirms
Torch 2.0.1+cu118 was loaded from the dedicated Conda prefix. This did not
resolve material initialization. The final optional asset-load diagnostic is
recorded separately; neither diagnostic changes baseline defaults.

The first five probes used the default OG GPU-dynamics macro, but all stopped
before physics/scene initialization. Subsequent task probes explicitly enable
GPU dynamics to match eval.py and add required segmentation to the cached robot.
This does not retroactively turn the earlier engine timeouts into task tests.
Future series save an immutable copy and SHA256 of their probe entrypoint.

The final asset-load diagnostic also timed out at 120 s with the same material
initialization stack (`results/original/startup/20260915T181418107472Z/`).
Its whole-GPU usage was 1572 → 1535 MiB; there were no remaining simulator or
GPU compute processes at the final check. Monitored external file changes were
zero. OMP, import-order and asset-load diagnostic flags are not adopted as fixes.
The engine remains unresolved; do not launch scientific trials or claim a stable
simulator. The collected stack and immutable final probe are available for a
focused native-runtime investigation without repeating the artifact search.

## Follow-up: exact native boundary and syscall tracing

See [native_minimal_diagnosis.md](native_minimal_diagnosis.md) for the subsequent
bounded, instrumented comparisons. The block is `omni.usd.add_hydra_engine`
before scene loading and reproduces without OG Python imports. Syscall tracing
found external OptiX cache and telemetry runtime files missed by the earlier
home-directory monitoring; both locations are now redirected into the project.
The prior fresh-cache probe therefore did not isolate OptiX cache state.
Baseline remains FAIL; root cause is not yet established.
