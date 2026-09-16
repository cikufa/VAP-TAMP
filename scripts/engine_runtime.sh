#!/usr/bin/env bash
# Source in Bash. Native engine is a project-local OmniGibson dependency.
source "$(dirname -- "${BASH_SOURCE[0]}")/project_runtime.sh"
export CONDA_PREFIX="$VAPTAMP_ROOT/.runtime/envs/vaptamp-repro"
export PATH="$CONDA_PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$CONDA_PREFIX/lib"
source "$VAPTAMP_ROOT/.runtime/native/isaac-sim/setup_conda_env.sh"
# Prefer the dedicated environment's packages over bundled Python dependencies.
# Include the project-local OmniGibson checkout explicitly. The Conda editable
# install records an absolute source path, which becomes stale if this otherwise
# self-contained repository is moved.
export PYTHONPATH="$VAPTAMP_ROOT/.runtime/OmniGibson:$CONDA_PREFIX/lib/python3.10/site-packages:$PYTHONPATH"
export XDG_CONFIG_HOME="$VAPTAMP_ROOT/.runtime/config"
export XDG_DATA_HOME="$VAPTAMP_ROOT/.runtime/user-data"
export CUDA_CACHE_PATH="$VAPTAMP_ROOT/.runtime/cache/cuda"
export __GL_SHADER_DISK_CACHE_PATH="$VAPTAMP_ROOT/.runtime/cache/nvidia"
export NLTK_DATA="$VAPTAMP_ROOT/.runtime/data/nltk"
export OMNIGIBSON_ASSET_PATH="$VAPTAMP_ROOT/.runtime/data/assets"
export OMNIGIBSON_DATASET_PATH="$VAPTAMP_ROOT/.runtime/data/og_dataset"
export OMNIGIBSON_KEY_PATH="$VAPTAMP_ROOT/.runtime/data/omnigibson.key"
export OMNIGIBSON_GPU_ID=0
mkdir -p "$XDG_CONFIG_HOME" "$XDG_DATA_HOME" "$CUDA_CACHE_PATH" "$__GL_SHADER_DISK_CACHE_PATH" "$NLTK_DATA"

# Native OptiX and telemetry do not follow the CUDA/GL cache settings.
export OPTIX_CACHE_PATH="$VAPTAMP_ROOT/.runtime/cache/optix"
export XDG_RUNTIME_DIR="$VAPTAMP_ROOT/.runtime/run"
mkdir -p "$OPTIX_CACHE_PATH" "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

# Audited on this i9-14900K workstation: five clean task launches on its
# efficiency cores, versus intermittent corruption/hangs without affinity.
# Only project launchers apply this to themselves and their descendants.
export VAPTAMP_CPU_AFFINITY="${VAPTAMP_CPU_AFFINITY-16-31}"
