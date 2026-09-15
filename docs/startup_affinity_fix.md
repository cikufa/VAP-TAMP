# Task startup: process affinity workaround

2026-09-15. The original Conda Python 3.10.21 / OG 1.0 / Isaac 2023.1.1
installation passed five consecutive `bringing_water` task launches when the
process was restricted to CPUs 16–31 on this workstation. These are the
i9-14900K's efficiency cores according to the observed Linux topology
(one logical CPU per core, 4.4 GHz maximum, versus paired performance cores).

`scripts/engine_runtime.sh` now exports `VAPTAMP_CPU_AFFINITY=16-31` unless
explicitly overridden. `startup_series.py` and `run_original_episode.py` apply
it only to their own process and descendants. No CPU has been disabled; no
BIOS, microcode, driver, CUDA, Vulkan or other application setting was changed.
On another machine this CPU list must be re-audited. An explicitly empty value
disables the setting for a diagnostic comparison.

## Evidence

All startup run IDs below are under `results/original/startup/`.

| Run | Hypothesis / change | Result |
| --- | --- | --- |
| `20260915T204050478345Z` | Instrument native USD traversal; normal affinity | Two task passes, then timeout while rendering during Fetch dummy-joint creation |
| `20260915T204354225164Z` | Limit Kit task workers to 8 | Native segmentation fault during robot registration |
| `20260915T204458739776Z` | Bundled Python 3.10.13, same project packages | Segmentation fault during SimulationApp UI preparation |
| `20260915T204618490338Z` | Bundled Python plus vendor libcarb preload | Bounded startup timeout |
| `20260915T204931522467Z` | Original Conda runtime, process affinity 16–31 | Five consecutive task/camera/step/shutdown passes |

The official image's own userspace also timed out during UI preparation with
normal affinity: `results/original/image_renderer/20260915T204759952914Z`.
It returned from Hydra initialization, so this differs from the original
inotify material-initialization stall. The full image remains diagnostic only.

The successful five-run series includes actual task reset, RGB 128×128×4,
semantic and instance segmentation, ten simulation steps, and parent-observed
clean exit. Wall times including cleanup: 38.38, 38.59, 36.35, 38.67, 36.37 s.
All report zero remaining simulator processes and zero changed monitored
external files. GPU totals fluctuate with desktop activity; no simulator
process remains to retain GPU allocations after these probes.

## Interpretation and limits

Affinity is an empirically validated workaround, not proof of a particular
hardware defect or a complete diagnosis of the earlier string/list corruption.
The exception originally arose from code that initializes a local list and
only appends/concatenates lists. Later failures varied between native crashes
and render stalls. Neither changing interpreter nor reducing Kit workers alone
stabilized the tested launches. Restricting the process to the efficiency cores
did. This can reflect a core-specific or concurrency-sensitive problem; the
five-run check cannot distinguish those explanations.

Intel documents instability affecting some 13th/14th-generation desktop CPUs:
[Intel support article 000102331](https://www.intel.com/content/www/us/en/support/articles/000102331/processors.html).
That is relevant background, not evidence that this specific processor has
that fault. No firmware or system changes were attempted.

Traversal instrumentation is opt-in (`VAPTAMP_TASK_LOAD_TRACE=1`) and records
source/code hashes and types at the failing frame. The normal runtime keeps
the vendor traversal function unchanged.
