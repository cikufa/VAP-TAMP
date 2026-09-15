# Renderer startup fixed: exhausted inotify watch quota

2026-09-15. The original OG 1.0 / Isaac 2023.1.1 / Kit 105.1.2 stack now
initializes RTX on the unchanged NVIDIA 580.105.08 driver.

## Cause and fix

The user's Linux inotify watch quota was exhausted. The configured maximum is
65,536 watches; process FD inspection observed a sum of 65,563 (shared inherited
FDs can cause double counting). Two VS Code watcher processes accounted for
42,559 and 19,926 watches. Earlier engine logs explicitly reported inotify
`errno=28` failures. The large downloaded/generated runtime tree consumed the
editor's watch budget. Disabling Kit's **extension** watcher did not eliminate
the renderer's separate need for filesystem watches.

Added `files.watcherExclude: {"**/.runtime/**": true}` to:

* `VAP-TAMP-clean/.vscode/settings.json` (tracked repository setting).
* `/home/shekoufeh/VAP_TAMP/.vscode/settings.json` (the enclosing open workspace).

VS Code applied the setting without restart: its 42,559-watch process dropped
to 790 watches. No applications were killed and no sysctl/driver/system package
was changed. A probe with the same watcher-enabled settings that had just hung
then returned from `add_hydra_engine` in 0.73 s.

## Minimal acceptance

`results/original/startup/20260915T192701365926Z`:

* Native renderer ready: 7.72 s.
* RGB saved: 7.96 s, `probe_1/native_rgb.npy`, shape 64×64×3.
* Physics advanced: 8.10 s, simulation time 0.06666667 s.
* Explicit `SimulationApp.close()` followed by native shutdown log and exit 0.
* No timeout or remaining probe process. Host settings unchanged.

The original summary marked this run false because the harness expected an event
**after** `close()`. Isaac's `SimulationApp.DEFAULT_LAUNCHER_CONFIG` sets
`fast_shutdown=True`, documented to exit the process immediately. The harness
now validates parent-observed zero exit, shutdown request/log, no timeout, and
required RGB/physics events. It does not waive scene or camera checks.
The raw summary is preserved; the acceptance assessment and watch evidence are
in `results/original/watch_quota_fix/evidence.json`.

The RGB smoke also needed `rep.orchestrator.step(rt_subframes=4)` before reading
its annotator; app updates alone returned an empty buffer. This is a smoke-test
correction, not a change to VAP-TAMP or OmniGibson algorithms.

## Additional isolation performed

The complete checksum-verified official OG 1.0 image was assembled under
`.runtime/og-image-rootfs`. Existing bubblewrap ran its OS/Python userspace with
selected host NVIDIA libraries, without Docker or system installation. That
renderer also stalled while the watch quota was exhausted. Its first probe
lacked optional nvcuvid injection; the launcher now includes it. The image is
retained as a diagnostic option and is not required by the fix.

Image source/download/execution helpers: `prepare_og_image.py`, `run_og_image.py`,
`image_renderer_smoke.py`. Original downloaded assets and caches were retained.
