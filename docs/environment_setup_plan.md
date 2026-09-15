# Environment setup plan — pre-install audit

Audit date: 2026-09-15. No packages, simulator, or datasets installed at this checkpoint.
Project: `/home/shekoufeh/VAP_TAMP/VAP-TAMP-clean` (new clean official clone).
Upstream: https://github.com/aoloo-r/VAP-TAMP.git, branch `main`,
commit `39a52b0e10427ce91ddf3c1a177d3f4f782a61c3`.
Experiment branch: `vaptamp-handoff-experiment`. No remote push.

## Machine

Ubuntu 22.04.5; approximately 62 GiB RAM; NVIDIA RTX 4090, 24 GiB VRAM.
Driver 580.105.08 advertises CUDA driver compatibility through 13.0.
System nvcc is 11.5; neither will be changed. Initial free disk: 196 GiB.
Existing Conda installation: `/home/shekoufeh/miniconda3`; use its environment
manager only. Do not install into or execute research using base or existing environments.
No Isaac Sim was found at the conventional user installation path; this is not
an exhaustive search of the entire machine.

## Compatibility decision

The README says to activate `omnigibson`, but the supplied `vlm-tamp/env.yml`
actually names `vlm-tamp`, pins Python 3.9, torch 1.12.1 and torchvision 0.13.1,
and omits OmniGibson. The README's `requirements.txt` is absent. Neither paper
nor release pins an OmniGibson commit or asset version. Do not represent a
reconstructed environment as the authors' exact environment.

The initial compatibility candidate is **OmniGibson v1.0.0**, commit
`282adda4c2cdba4bc8d3c1a4b524d3ff94453f3a`: its source contains the imported
`RobotCopy`, `PlanningContext`, and starter semantic primitives. v0.2.1 lacks
the requested starter-primitives file. Newest OmniGibson is not selected.
This is a static API-based inference (class D), pending runtime validation.

| Component | Proposed environment / evidence | Status |
| --- | --- | --- |
| Python | 3.10, matching the Isaac Sim 2023.1 generation required by OG v1.0.0; exact patch must match acquired runtime | Compatibility departure from repository's 3.9 |
| Conda | Prefix `.runtime/envs/vaptamp-repro`, display name `vaptamp-repro` | New; project local |
| OmniGibson | v1.0.0 at SHA above, editable source in `.runtime/OmniGibson` | Candidate, not installed or validated |
| BEHAVIOR | BEHAVIOR-1K OG dataset `1_0_0`; BDDL `~=3.5.0` per OG setup.py | Versioned assets; task membership must be checked |
| Native engine | Isaac Sim 2023.1.1, per pinned OG install instructions, in `.runtime/isaac-sim-2023.1.1` | Availability and exact distribution size unresolved |
| PyTorch | Repository requests 1.12.1 / torchvision 0.13.1; final simulation torch must agree with engine-bundled libraries | Not silently upgraded; unresolved until runtime acquired |
| CUDA runtime | Repository's pip torch pin does not specify a CUDA build. Expected legacy torch CUDA 11.x; exact engine torch/CUDA build must be read from runtime manifest | Driver maximum 13.0 is not the runtime requirement |
| Fast Downward | Vendored source at VAP-TAMP upstream SHA; existing C++ compiler and CMake, Release build | No separate dependency SHA is present |
| VAL | Vendored source at same SHA; CMake Release build at `vlm-tamp/VAL/build/linux64/Release` | README's bare `make` is insufficient before configuration |
| PDDL parser | PyPI `pddl`, API compatibility validated before freezing | Missing from supplied environment |
| Simulation VLM | Released `GPT4VAgent`, `gpt-4-turbo`; approved reproduction default `gpt-4o-2024-05-13`; requests, Pillow, torchvision, numpy | Credential authenticates; image calls currently blocked by exhausted API credit balance |
| Other VLM paths | `google-cloud-aiplatform` for optional Vertex Gemini 1.0 wrapper; `google-generativeai` for real-robot Gemini wrapper; requests for VLMViewGuide | Keep optional paths out of simulation imports where possible |
| Other sim packages | OG pinned requirements plus matplotlib, numpy-quaternion, transforms3d, PyYAML, requests | Resolve in dedicated environment only |
| Scene / robot | `Ihlen_0_int`, `store_firewood`, definition/instance 0, `fetch_behavior.yaml` / Fetch | Native released baseline selection |
| Required assets | Versioned OG robots/material assets, BEHAVIOR scene and firewood objects, BDDL activity definitions | No Detic/CLIP downloads needed for released simulation |
| ROS | Not imported by normal simulation path; real robot uses ROS2 bridge and ROS1 `rospy` manipulation modules | Not required for simulation |
| Docker | Source installation is documented by OG | Optional, not required |

Isaac Sim here is OmniGibson's native engine dependency, not a port of the task
to a different simulator. The old Omniverse Launcher installation route may
no longer be available; do not replace the engine with a current release to
work around that without documenting the resulting compatibility change.

## Downloads and storage

Verified by HTTP HEAD, without downloading bundles:

| URL | Compressed bytes | Decision |
| --- | ---: | --- |
| https://storage.googleapis.com/gibson_scenes/og_dataset_1_0_0.tar.gz | 22,321,609,648 (22.32 GB / 20.79 GiB) | Requires user's >~20 GB approval |
| https://storage.googleapis.com/gibson_scenes/og_assets_1_0_0.tar.gz | 663,239,083 | Allowed only after engine/version gate |
| Isaac Sim 2023.1.1 distribution | Not established | Obtain exact official archive, size and checksums before download |
| Conda, torch and supporting packages | Several GB expected; solver determines exact amounts | Project-local caches |

Archive + extracted assets + engine + environment + videos must fit remaining
disk. Extracted size is unknown, so free space is not yet certified sufficient.
Do not choose the smaller, unversioned 2023 dataset solely to avoid approval;
it is not the selected version. Prefer generation-pinned GCS URLs and hashes.

## Containment and installation sequence

1. Finish source/method audit and commit it before executing the release.
2. Set `CONDA_REGISTER_ENVS=false` (supported by installed Conda),
   `CONDA_PKGS_DIRS`, `CONDA_ENVS_PATH`, `XDG_CACHE_HOME`, `PIP_CACHE_DIR`, and
   `TMPDIR` to project-local `.runtime` paths. Disable Conda plugins and use
   explicit channels to avoid user-level plugin/cache writes. Do not change HOME.
3. Create the dedicated Python 3.10 prefix for planner checks; this alone is
   not a working simulator environment. Do not install unresolved GPU packages.
4. Build vendored planners using existing system build executables; smoke-test
   original firewood PDDL in isolated output directories.
5. Obtain exact historical engine and approval for the versioned >20 GB dataset;
   confirm disk needs and native library versions. Then finalize GPU dependencies.
6. Record the approved pinned model deviation. Load credentials only from environment or
   ignored local `.env`; never use credentials embedded in upstream source.
7. Configure released full verification flags and classical planning; preserve
   injection probabilities. Debug one episode, then five trials. No connector
   implementation until successful original simulation has been committed.

All downloaded engine files should reside in the project; native executable
components cannot live solely in Conda. Engine cache/log locations must also
be inspected before launch. Any unavoidable external writes require approval.
Do not delete existing outputs: create unique run directories and remove the
release's automatic recursive cleanup before any episode launch.

After actual installation, export `environment.yml`, `requirements_frozen.txt`
and a Conda explicit package list. `docs/environment_versions.md` must clearly
distinguish planner-only provisioning from simulator provisioning.

## Audit follow-up: source and engine acquisition

The user approved the 22.32 GB dataset download, conditional on compatibility
and disk checks. That approval is retained; do not ask again for the same bundle.

The original NVIDIA container tag returned HTTP 404 after anonymous registry
authentication. Stanford's official `stanfordvl/omnigibson:1.0.0` image remains
available, built 2024-03-18, linux/amd64, compressed total 10,704,289,561 bytes.
Its manifest digest is
`sha256:8611bfe0507505d3c5fdaec07c272b12d2a1f8a0a75b73b177da751086f13503`.
The original engine COPY layer is 8,937,203,082 bytes, digest
`sha256:a1b1e92d5165bfe6d5ac68453c2bbbb4a000882bc453e35b4a714c8cdae1a2d4`.
`scripts/fetch_historical_engine.py` downloads and verifies that archive only,
within the project, without a Docker daemon or executing image build commands.
Extracting the engine from this layer is an installation adaptation; later image
layers modify gym/numpy packaging, click and livestream configuration and must
be considered separately. It is not a full reconstruction of the Docker image.

The OG source clone at the selected SHA confirms the requested symbols, but
`Robot.get_obs()` returns `(observations, info)` while VAP-TAMP expects a dict.
A documented observation-unpacking compatibility fix is needed. This reinforces
that the exact original simulator commit remains unidentified.

The inherited login environment includes ROS PYTHONPATH. The project runtime
script now clears PYTHONPATH/PYTHONHOME and disables user site packages; exports
and the passing planner check were regenerated with that isolation in effect.

## Sources

- [Released environment](https://github.com/aoloo-r/VAP-TAMP/blob/39a52b0e10427ce91ddf3c1a177d3f4f782a61c3/vlm-tamp/env.yml)
- [Pinned OG installation](https://github.com/StanfordVL/OmniGibson/blob/282adda4c2cdba4bc8d3c1a4b524d3ff94453f3a/docs/getting_started/installation.md)
- [Pinned OG dependency metadata](https://github.com/StanfordVL/OmniGibson/blob/282adda4c2cdba4bc8d3c1a4b524d3ff94453f3a/setup.py)
- [Native engine archived release notes](https://docs.isaacsim.omniverse.nvidia.com/4.0.0/archived_release_notes.html)
- [Paper](https://arxiv.org/html/2604.26988v1), especially Section V-B.

## Installed follow-up (2026-09-15)

The native layer checksum passed and 18,916,022,685 regular-file bytes were
extracted project-locally. Native VERSION: `2023.1.1-rc.8+2023.1.688.573e0291.tc`,
Kit 105.1.2. Installed torch 2.0.1+cu118 / torchvision 0.15.2+cu118 match
its metadata, with Python 3.10.21 and NumPy 1.23.5. CUDA arithmetic and two
contained headless launches passed. No system CUDA or driver changes.

The 663,239,083-byte asset archive passed MD5 verification and expanded to
1,796,755,804 bytes. The approved dataset download passed its version-pinned
MD5 check; archive inventory and free-space check precede extraction. The user
explicitly accepted the bundled non-commercial academic research license; the
key was installed under `.runtime/data` without logging its value.

Observation tuple/segmentation compatibility changes are documented in
`compatibility_fixes.md`. The first launch wrote five external NVIDIA logs,
contrary to the project-only boundary. That incident was disclosed; structured
logs and document/cache tokens are now redirected. No external files were
deleted or restored.

Dataset extraction completed: 28,572,351,606 regular-file bytes, 66,320 files;
147,172,098,048 bytes were free before expansion. About 111 GiB remained
after extraction. The default Ihlen firewood task cache is absent; see
`asset_status.md`. Dataset installation alone is not baseline reproduction.
