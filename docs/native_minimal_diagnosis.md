# Native minimal-scene diagnosis — 2026-09-15

Scope: baseline acceptance only. No connector, scientific episodes, VLM calls,
model changes, simulator substitution, or VAP-TAMP algorithm changes.

## Instrumented boundary

The first blocking Python operation is `omni.usd.add_hydra_engine`, called by
`create_new_stage()` inside `SimulationApp.__init__`. The empty USD stage is
being opened before OmniGibson can load any configured scene. Instrumentation
wraps native methods in the diagnostic process only; installed sources are not
patched. The prior native debugger shows the main thread waiting in Carbonite
tasking from RTX Neuray/material initialization. That stack establishes a wait,
not its root cause.

## Comparisons

| Probe directory under results/original/startup | Variable | Observation |
|---|---|---|
| 20260915T183036378772Z | Instrumented default | Kit starts at 7.64 s; Hydra entry at 7.72 s never returns; 75 s limit |
| 20260915T183205716152Z | Constructor `sync_loads=False` | All three effective loading flags false; Hydra entry at 7.51 s never returns; 60 s limit |
| 20260915T183434498609Z | Project OptiX cache and runtime directory, strace | Hydra entry at 19.89 s; no return; 60 s limit |
| 20260915T183547708413Z | Carbonite worker count 4, same contained trace | Effective count 4; Hydra entry at 18.95 s; no return |
| 20260915T183320015261Z | File/network strace, default loading | Hydra entry at 20.89 s; no return; 60 s limit, tracing overhead |

Two launch requests were refused before native execution: one matched the shell's
inline source text as a stale process; one was issued while the preceding probe
was still running. These are not additional simulator failures.

The old asynchronous-loading CLI experiment was inconclusive: the native
constructor resets these flags. The new constructor-level comparison measures
the effective settings after that reset and rules out those flags as a fix in
this environment.

## Asset and cache evidence

The syscall trace reads dataset metadata during OG import, but reaches the stall
without loading a BEHAVIOR scene. It opens bundled local MDL paths and initializes
Vulkan on the RTX 4090. No BEHAVIOR scene download or Nucleus connection was
observed as the blocking operation. The observed external HTTPS activity belongs
to the telemetry transmitter, which exits before the still-stalled simulator.

The trace uncovered previously unmonitored persistent writes: OptiX cache files
under `/var/tmp/OptixCache_shekoufeh` and telemetry control files under
`/run/user/1003`. Earlier home-directory metadata checks did not cover these.
Existing external files were not removed or restored. `engine_runtime.sh` now
sets project-local `OPTIX_CACHE_PATH` and `XDG_RUNTIME_DIR`; kernel device/proc
and shared-memory operations are distinct from project data/cache files.
The earlier fresh CUDA/GL/Kit cache test did **not** isolate the OptiX cache.
These two containment corrections are a required combined environmental change,
not a clean one-variable causal test.

## Minimal smoke and acceptance gates

`VAPTAMP_MINIMAL_SCENE=1` requests the native OG `Scene` class (the supported
empty scene in OG 1.0), disables its skybox, adds a procedural cube and floor,
steps ten times, captures viewer-camera RGB, and shuts down. No robot or
BEHAVIOR scene is requested. This code has not yet reached scene construction;
there is no RGB/physics pass to report.

Stop at layer 1 until startup and the minimal smoke pass. Arbitrary BEHAVIOR,
bringing_water, robot/cameras, and one scripted primitive remain untested.

## Credential and model

The released simulation path requires an OpenAI API key with access to
`gpt-4-turbo` and its image-input Chat Completions endpoint.

* `vlm-tamp/gpt4v.py:15` reads `OPENAI_API_KEY`; line 17 rejects an empty value.
* Line 24 selects `gpt-4-turbo`; lines 61 and 128 use that model in payloads.
* Lines 77–80 put the key in the bearer header and POST to
  `https://api.openai.com/v1/chat/completions`.
* `vlm-tamp/eval.py:120` constructs `GPT4VAgent` at module scope before the
  environment. The standalone smoke does not import this module.
* `scripts/run_original_episode.py:30` loads project `.env` without overriding
  existing environment values; lines 31–32 check the key, then the child inherits
  it. `gpt4v.py` itself does not load `.env`.

No key is needed for the diagnostic probes; no API request has been made here.

The contained syscall trace confirms OptiX database creation under project
`.runtime/cache/optix`. The earlier stale external cache is therefore not
necessary to reproduce the wait. This bounded test alone does not prove that
every possible first-run compilation has completed. Successful persistent file
creation outside the project was not found in the filtered contained trace
(excluding kernel/device and shared-memory operations).

The task worker setting is `/plugins/carb.tasking.plugin/threadCount`, verified
in the installed native binary and by reading effective settings. NVIDIA's
[Carbonite tasking documentation](https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/docs/tasking/TaskingSettings.html)
describes this worker-count control. Four workers did not resolve the stall.

## Current conclusion

The same native engine and `omnigibson.kit`, launched **without importing OG**,
reproduce the block (`20260915T183702579272Z`, Hydra entry 18.11 s, 60 s bound).
This test does not need dataset metadata, a task, robot, or API key. It isolates
OG Python import-time effects but retains the engine's bundled extensions and
Python runtime, so it cannot exclude native packaging or extension issues.
A telemetry fork timeout also appears in this straced run; the renderer wait
already occurs independently in runs where telemetry successfully exits.
Cgroup PID limits were not exhausted (all inspected `pids.events` max counters
zero). Do not infer a host process-limit cause from that telemetry message.

`results/original/native_vulkan_summary.txt` records successful Vulkan device
enumeration: NVIDIA RTX 4090, driver 580.105.08, Vulkan 1.4.312. Native Kit selects
the same GPU. This is not an RTX material-rendering test or certification of
this old engine against the installed driver. No host driver/settings changed.

| Candidate | Evidence / remaining uncertainty |
|---|---|
| Specific BEHAVIOR scene or missing Ihlen instance | Not necessary: block precedes scene load and reproduces without OG import |
| Dataset download / Nucleus scene paths | No task asset request at blocking boundary; native-only reproducer does not require dataset |
| Existing cache corruption/lock | Fresh project OptiX cache also stalls; earlier separate Kit/CUDA/GL cache test stalled. Not an exhaustive cache proof |
| Sync material/asset loads | Constructor-level false setting verified; same block |
| Long first-run compilation | Previous 900 s probe and low CPU activity oppose a simple warmup explanation; no completion evidence. That previous probe retained external OptiX cache |
| Carbonite worker count | Four workers reproduce; count confirmed in settings |
| OG version/import mismatch | Pinned OG 1.0/Isaac 2023.1.1 match nominal requirement; same native block without OG Python imports |
| GPU/driver/native engine or extension compatibility | Still unresolved; Vulkan discovery passes but native RTX/Neuray initialization does not |

**Root cause remains unresolved.** The precise reproducible boundary is native
RTX Hydra attachment, with the earlier debugger placing its wait in
Neuray → Carbonite tasking. No successful minimal RGB render, simulation step,
or clean native shutdown has been demonstrated. Higher layers remain stopped.
All completed timed-out probes were terminated and their process groups checked.
Timeout exits are failures, not clean shutdowns. Logs, immutable probe copies,
settings, syscall traces and summaries are retained under the listed directories.

## Reproduction

From the clean clone, in Bash:

```bash
source scripts/engine_runtime.sh
ulimit -c 0
VAPTAMP_NATIVE_TRACE=1 VAPTAMP_MINIMAL_SCENE=1 \
  python scripts/startup_series.py --count 1 --timeout 60
```

Use `VAPTAMP_NATIVE_STRACE=1` for file/network tracing (noticeable startup overhead).
The optional native-only diagnostic is `VAPTAMP_NATIVE_WITHOUT_OG=1`; it is an
engine isolation test, not a minimal OG acceptance pass. Do not combine it with
`VAPTAMP_MINIMAL_SCENE=1`. Instrumentation/worker/loading overrides are diagnostic
only and have not been adopted by the baseline evaluator.

Validation: diagnostic Python sources parse; runtime shell passes `bash -n`;
`git diff --check` passes. Native probes above are the relevant runtime checks.
