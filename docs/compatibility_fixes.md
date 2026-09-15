# Local compatibility changes

These changes are independent of the handoff hypothesis. Original action
probabilities, PDDL and successful VLM query semantics are preserved.

| Change | Reason | Validation |
| --- | --- | --- |
| Clear inherited ROS PYTHONPATH and user site | A new Conda prefix alone still saw external packages | Clean exports; original planner smoke passes |
| Python 3.10, torch 2.0.1+cu118, torchvision 0.15.2+cu118 | Exact native engine metadata, unlike incomplete release env | CUDA arithmetic passed on RTX 4090; OG import passed |
| Remove unused eager Vertex import from eval.py | Optional module constructs Gemini client during import, even on GPT path | Static import trace; no replacement endpoint |
| Unpack OG observation tuple | OG 1.0 returns `(data, info)` | Focused identity check preserves original pixel data |
| Read segmentation ID-to-name mapping | IDs are a registry, no longer `scene.objects[id-1]` | Sparse-ID test includes an out-of-range-for-list value |
| Enable existing primitive's required segmentation modalities | Missing from versioned default Fetch config | Source API/config audit; scene test pending |
| Environment variables for existing flags, seed, trial count and log path | Reproducible debug/pilot launch without repeated code edits | Defaults preserved; runtime validation pending |
| Unique third-person output directory | Upstream recursively deletes prior frame directory | Removed deletion call; no prior outputs removed |
| Fail on absent key, HTTP error or empty response | Upstream could return invented affirmative answers on API failure | HTTP 429 and empty-response tests; successful yes/no/skip preserved |
| Two upstream credential literals removed | Never use embedded upstream credentials | Environment lookups only; no history rewrite or remote push |

Five focused tests in `tests/test_compatibility.py` pass. They extract the actual
functions from the source AST because importing eval.py starts an experiment.
These are compatibility tests, not mock simulation results or VLM evaluations.

## Historical engine installation

Official Stanford OG 1.0.0 container digest and layer hashes are in
`environment_setup_plan.md`. The verified native engine layer was extracted
with Python tarfile's data filter into `.runtime/native/isaac-sim`.
Its `VERSION` is `2023.1.1-rc.8+2023.1.688.573e0291.tc`, the build distributed
in that official release. Kit is 105.1.2; Python ABI is 3.10. This is not a
claim that the original VAP-TAMP authors used this exact environment.

Torch/torchvision are installed inside Conda; the engine also ships its own
Python extensions and libraries. `engine_runtime.sh` gives the dedicated
environment's site-packages priority. This setup uses the native engine source
layer, not the complete Docker image and its system packages.

The first startup probe segfaulted during `SimulationApp._prepare_ui` on an app
update. Cause is not yet established. Do not infer a driver incompatibility
solely from this symptom, and do not change host drivers or system CUDA.

## External-log containment incident

At the first startup probe (2026-09-15 17:09 UTC), portable mode and the main-log
path did not redirect NVIDIA structured logs. Five files were written under
`/home/shekoufeh/.nvidia-omniverse/logs`:

- `omni.kit.extension.log`
- `omni.kit.sysinfo.log`
- `omni.replicator.extinfo.log`
- `omni.processlifetime.log`
- `omni.kit.internal.log`

This violated the requested project-only write boundary and was disclosed to
the user. No external files were deleted or restored. Subsequent launch code
uses the documented `/structuredLog/logDirectory` override, global log/cache
token overrides, and project-local document tokens. Core dumps are disabled
for diagnostic child processes. External-log timestamps/sizes are compared
around the contained probe. This is a containment fix, not a method change.

Source: [NVIDIA structured logging settings](https://docs.omniverse.nvidia.com/kit/docs/carbonite/158.2/docs/structuredlog/OmniTelemetry.html).

Two subsequent contained native probes passed: one under gdb, one without it
(`.runtime/engine-gdb-probe.log`, `.runtime/engine-contained-plain-probe.log`).
Both printed `NATIVE_ENGINE_LAUNCH_OK` and shut down normally. External log
sizes/timestamps remained unchanged. This does not establish the cause of the
first crash or certify a scene, camera, or manipulation episode.

The scene probe later stalled during engine UI startup, before loading a task,
with filesystem watcher allocation errors (errno 28). Disk remained >100 GiB
free. A bounded retry disables extension hot-reload watchers using
`/app/extensions/fsWatcherEnabled=false`; no host inotify limits are changed.
The missing cached task is independently established by archive inventory.

Source: [NVIDIA extension settings](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/107.2.0/guide/extensions_advanced.html).

Optional `repro_trace.py` instrumentation writes chronological JSONL inside the
episode sandbox. It preserves request prompts/images, raw response bodies,
plans, verifier facts and symbolic updates. Third-person frame directories are
per-trial to avoid overwriting earlier trial frames. No decisions or injected
failure probabilities depend on the logger. Runtime validation remains pending.

The watcher-disabled retry also stalled before task initialization. The final
sole-process retry (`.runtime/original-scene-final-probe.log`) reached the same
UI startup point and was terminated by its 45 s timeout plus 5 s kill grace
(exit 137). No task or camera success marker was emitted. Watcher suppression
removed the watcher errors but did not fix the stall. No probe processes remain.
The five external log sizes/timestamps still match the post-first-launch values.
Native startup remains intermittent and unresolved; a future session should
collect a bounded debugger trace before attempting an episode.
