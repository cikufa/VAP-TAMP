# Omniverse / RTX compatibility audit

Date: 2026-09-15. Starting checkpoint: `9dc6b19`.
Scope: native `omni.usd.add_hydra_engine()` → RTX/Neuray initialization only.
No changes to host driver, CUDA, Vulkan, packages, Docker configuration, or the
working GoFlow/Isaac installation. No higher-layer simulation or API calls.

## Findings at a glance

**There is no exact OmniGibson/Kit pin in the upstream VAP-TAMP release.** Our
OG 1.0 / Isaac 2023.1.1 pairing matches that OG release's installation guidance,
but it is a reconstruction, not a recovered authors' lockfile. Driver 580.105.08
is substantially newer than this stack's R525/R535-era evidence. Its successful
Vulkan enumeration does not establish compatibility with Kit's RTX renderer.
Neither an explicit certification nor an explicit prohibition of this exact
580.105.08 + Kit build combination was found.

**No safe userspace fix was demonstrated.** One 60-second bundled-Python probe
reproduced the stall. The next recommended action is a single minimal-renderer
test of the complete pinned OG 1.0 container on this host's existing driver,
through an authorized GPU-enabled Docker runtime. Current daemon access is
denied, and NVIDIA container integration is not established. Container success
is therefore **unknown**, not PASS and not ruled out.

## 1. What VAP-TAMP actually specifies

Upstream reference: `39a52b0e10427ce91ddf3c1a177d3f4f782a61c3`.

* [Planning README](https://github.com/aoloo-r/VAP-TAMP/blob/39a52b0e10427ce91ddf3c1a177d3f4f782a61c3/vlm-tamp/README.md)
  links to the moving OG installation page and suggests installing from source;
  it supplies no OG tag, commit, Kit build, or Isaac Sim version.
* [Upstream env.yml](https://github.com/aoloo-r/VAP-TAMP/blob/39a52b0e10427ce91ddf3c1a177d3f4f782a61c3/vlm-tamp/env.yml)
  specifies Python 3.9, Torch 1.12.1, and torchvision 0.13.1. It omits OG and
  Isaac/Kit. The README refers to `requirements.txt`, absent at that location.
* Our root `environment.yml` and `requirements_frozen.txt` are local generated
  environment records. They must not be presented as upstream pins.

Consequently the answer to “the exact required OG commit” is **not specified**.
The installed candidate is OG **v1.0.0**, commit
`282adda4c2cdba4bc8d3c1a4b524d3ff94453f3a`, with a clean source tree. The prior
static API rationale is recorded in `environment_setup_plan.md`: v1.0 supplies
the imported starter primitives/RobotCopy/PlanningContext; inspected v0.2.1 did
not supply the requested starter-primitives file. This is compatibility evidence,
not proof of the authors' version. We did not reopen task/planner behavior here.

## 2. Exact OG → Isaac → Kit pairing

[OG v1.0 installation instructions](https://github.com/StanfordVL/OmniGibson/blob/v1.0.0/docs/getting_started/installation.md)
identify Isaac Sim **2023.1.1** and a Python **3.10** environment.
The [versioned development Dockerfile](https://github.com/StanfordVL/OmniGibson/blob/v1.0.0/docker/dev.Dockerfile)
uses `FROM nvcr.io/nvidia/isaac-sim:2023.1.1`.
The [production Dockerfile](https://github.com/StanfordVL/OmniGibson/blob/v1.0.0/docker/prod.Dockerfile)
builds on the OG development image. OG's `_launch_app` checks a minimum Isaac
version of 2023.1.1; that lower-bound check is not a promise of compatibility with
all future Isaac releases.

Measured from the acquired distribution and native startup log:

| Component | Exact installed identity |
|---|---|
| OG | 1.0.0 / `282adda4c2cdba4bc8d3c1a4b524d3ff94453f3a` |
| Isaac Sim | `2023.1.1-rc.8+2023.1.688.573e0291.tc` |
| Omniverse Kit | `105.1.2+release.133510.b82c1e1e.tc` |
| Carbonite kernel | `158.3+release158.tc9506.b2fcff1c` |
| Dedicated Conda Python | 3.10.21 |
| Engine-bundled Python | 3.10.13 |
| Host | Ubuntu 22.04.5, RTX 4090, NVIDIA 580.105.08 |

Kit is bundled by Isaac, not independently selected by pip/Conda. The detailed
build suffix comes from the binary's own startup log, not an OG Kit pin.
Evidence: `results/original/startup/20260915T183036378772Z/probe_1/kit.log`, first
startup record; `.runtime/native/isaac-sim/VERSION`.

Acquisition provenance: official `stanfordvl/omnigibson:1.0.0`, image manifest
`sha256:8611bfe0507505d3c5fdaec07c272b12d2a1f8a0a75b73b177da751086f13503`,
created 2024-03-18. Only its native engine layer was extracted, digest
`sha256:a1b1e92d5165bfe6d5ac68453c2bbbb4a000882bc453e35b4a714c8cdae1a2d4`.
The complete image's layers total **10,704,289,561 compressed bytes**.
This extraction is **not equivalent to running the complete container**: its
OS libraries, preconfigured Conda environment and later Dockerfile adjustments
are not all reconstructed. No accidental upgrade to a different Kit version
was found. Python/Torch differ from VAP-TAMP's incomplete environment intentionally
for the OG 1.0 candidate; reverting only to Python 3.9 is not a valid Isaac 2023.1.1 fix.

## 3. Official support evidence and its limits

| Evidence | What it establishes | What it does not establish |
|---|---|---|
| Versioned OG v1.0 installation page | Linux Ubuntu 20.04+ and Isaac 2023.1.1 | An exhaustive kernel/driver certification matrix |
| Official OG image configuration | `MIN_DRIVER_VERSION=525.60.11`, `NVIDIA_DRIVER_CAPABILITIES=all` | A renderer-tested range or validated maximum; metadata is not certification |
| [NVIDIA renderer microservice 1.0](https://archive.docs.nvidia.com/ace/omniverse-renderer-microservice/1.0/ucs-ms/README.html) | Related Kit 105.1.2 build `release.135279.09b309e7`; recommends R535, explicitly excludes R545; DLSS frame-generation stalls documented | The same Isaac build, or a blanket R580 exclusion |
| [Isaac 4.2 archived requirements](https://docs.isaacsim.omniverse.nvidia.com/4.2.0/installation/requirements.html) | Ubuntu 20.04/22.04; Linux minimum/recommended 535.129.03 for **4.2** | Exact requirements of 2023.1.1 |
| [Current NVIDIA technical requirements](https://docs.omniverse.nvidia.com/dev-guide/latest/common/technical-requirements.html) | R580 appears in current validated-driver tables; newer drivers are not automatically validated | Retrospective certification of Kit 105.1.2 |

The historical 2023.1.1 requirements endpoint could not be recovered during this
bounded audit: `https://docs.isaacsim.omniverse.nvidia.com/2023.1.1/installation/requirements.html`
returned 404. The old `docs.omniverse.nvidia.com/isaacsim/latest/...` link redirects
to current documentation; several versioned alternatives were unavailable.
**A complete officially supported Linux/driver range for the exact Kit build
therefore remains unverified.** Do not silently substitute the 4.2 table or claim
that every driver >=525.60.11 is renderer-compatible. No verified upper bound was found.

580.105.08 is numerically far newer than the R525 image threshold and R535
recommendations for this generation. It is a plausible compatibility variable,
but no controlled driver comparison has demonstrated causation. The current
NVIDIA page's ARM Hydra issue is not evidence for this x86_64 machine; its newer
Kit/R595 restrictions also do not describe this exact combination.

DLSS-G is already disabled in OG's versioned Kit configuration
(`rtx-transient.dlssg.enabled=false`). Thus the related microservice's known
workaround is already present; we did not run a redundant probe for it.

## 4. Isolated installations and container feasibility

An OG 1.0 + Isaac 2023.1.1 environment can be assembled project-locally without
installing host CUDA or changing the driver; the existing candidate demonstrates
availability, not working rendering. Conda isolates Python packages but still
uses host graphics/driver libraries. The original NGC 2023.1.1 image tag was
unavailable during acquisition; the official Stanford image supplied the engine.

A newer official pairing exists: [OG v1.1 release notes](https://github.com/StanfordVL/BEHAVIOR-1K/releases/tag/v1.1.0)
recommend Isaac 4.1 and explicitly drop 2023.1.1 compatibility. They also change
NumPy interfaces to Torch tensors, pose APIs and IK. Installing that pair in a
separate environment is feasible in principle, but is a substantive fidelity
and migration decision, not a drop-in repair. Kit must remain bundled with its
Isaac release; do not replace individual RTX/Neuray libraries across versions.
No new stack was installed in this audit.

[NVIDIA Container Toolkit documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/docker-specialized.html)
explains that driver libraries are supplied to the container and `graphics` is
required for Vulkan. A container does not replace the host kernel driver with
R535. [CUDA backward compatibility](https://docs.nvidia.com/deploy/cuda-compatibility/latest/why-cuda-compatibility.html)
supports using older CUDA applications on newer drivers, but does not certify
Omniverse's graphics/RTX/OptiX path. **The expected userspace container might work
with 580.105.08; actual success is untested.**

Machine checks:

* `/usr/bin/docker` exists; `docker info` fails with permission denied on
  `/var/run/docker.sock` (root:docker, mode 660). No socket/group changes made.
* `nvidia-container-cli` and `nvidia-container-runtime` are not on PATH; no CDI
  configuration was found in the standard inspected directories. This does not
  prove that the inaccessible daemon has no integration; its runtimes could not
  be queried.
* Rootless Docker helpers exist, but `newuidmap` is absent from PATH and GPU
  integration is not established. Starting another daemon is not a demonstrated
  ready-to-use workaround. No daemon was started or system setup performed.

## 5. Single bounded compatibility experiment

Hypothesis: Conda interpreter/library precedence, rather than the engine build,
causes the native stall. `scripts/vendor_python_runtime.sh` uses the engine's
Python 3.10.13, `setup_python_env.sh`, and the vendor `libcarb.so` preload instead
of Conda's interpreter/library paths. This is a process-local alternative; the
baseline launcher is unchanged. No OG import, task, robot or VLM is involved.

```bash
source scripts/vendor_python_runtime.sh
ulimit -c 0
VAPTAMP_NATIVE_WITHOUT_OG=1 VAPTAMP_NATIVE_TRACE=1 \
  .runtime/native/isaac-sim/kit/python/bin/python3 \
  scripts/startup_series.py --count 1 --timeout 60
```

Result: **FAIL**, native stage attachment blocks again at 7.150 seconds. Kit
startup itself returned at 7.063 seconds. No RGB frame or physics step reached.
The timeout plus cleanup took 67.91 seconds. No remaining probe processes.
Artifacts: `results/original/startup/20260915T190622061606Z/` (immutable source,
phases, Kit log, console log and summary). This was the only new renderer launch
in the compatibility audit. No repeat with the same settings was run.

The smoke path now explicitly requests a 64×64 RGB buffer, one physics step and
clean close **after** native startup. These operations remain unexecuted because
Hydra never returns. Their presence in code is not an acceptance pass.
GoFlow processes concurrently used about 10.8 GB GPU memory; total usage was
about 12.2 GB. They were untouched. This limits attribution of the result as a
fully controlled comparison; no claim of GPU memory exhaustion is made.

No fix qualified for adoption, so the success-conditioned sequence of higher
layers did not begin. No baseline acceptance or connector experiment was run.

## 6. Candidate decision table

| Candidate | Expected compatibility | VAP-TAMP fidelity | Risk to existing machine | Effort | Recommendation |
|---|---|---|---|---|---|
| Revert to upstream Python 3.9 / Torch 1.12.1 | Does not supply required Isaac 2023.1.1 Python 3.10 runtime | Matches partial file, not an established simulator stack | Low if isolated | Low–medium | Reject as an unsupported repair |
| Current OG 1.0 / Kit 105.1.2 with bundled Python | Nominal pairing; bounded renderer test failed | Preserves selected OG/Kit candidate | Low, project-local | Low; tested | Do not adopt as a fix |
| Complete digest-pinned OG 1.0 container + current host driver | Canonical userspace pairing; R580 rendering still unverified | Best preservation of selected generation | Low when run with limited mounts; needs authorized GPU runtime access | Medium; 10.7 GB compressed image | **Recommended next test** |
| Separate OG 1.1 / Isaac 4.1 environment | Official pairing, not proven here on R580 | API/IK changes require revalidation | Low if fully isolated | High | Defer; not a drop-in fix |
| Host driver change toward historical R535 generation | Historical evidence improves, exact modern-host compatibility unverified | Preserves old application stack | High for working GoFlow/Isaac | High, admin/reboot | Not recommended while container option remains untested; never performed |

## One next action

**Run one 60-second minimal RTX acceptance probe in the complete official
`stanfordvl/omnigibson@sha256:8611bfe0507505d3c5fdaec07c272b12d2a1f8a0a75b73b177da751086f13503`
container using this host's existing driver, through an authorized GPU-enabled
Docker runtime.** Current account/runtime access must be made available before
this can be executed; this audit does not change it.

Use the image's own `/isaac-sim` and Python environment, not the extracted engine
bind-mounted over them. Mount only the smoke script and project output/cache
directories, set graphics/compute/utility driver capabilities, omit host home and
Docker-socket mounts, and record the image digest and internal loaded-library
paths. Bound startup at 60 seconds plus cleanup. Perform the empty-stage → Hydra
→ RGB → physics step → clean-exit check only. A successful `nvidia-smi` in the
container is insufficient. Prefer an otherwise idle GPU window; do not terminate
GoFlow to obtain one.

If that test fails at the same native boundary, preserve the container trace for
an upstream NVIDIA compatibility report before considering a machine-wide driver
change. If it passes, commit the working environment recipe, then advance through
the user's ordered acceptance layers, stopping at the first failure.

Local machine/version evidence: `results/original/compatibility_audit/facts.json`.
Validation: diagnostic Python syntax, shell syntax, and `git diff --check`; no
scientific result is implied by these checks.
