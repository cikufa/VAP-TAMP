#!/usr/bin/env bash
# Source this file to contain runtime state without changing the user's HOME.
VAPTAMP_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export VAPTAMP_ROOT
export CONDA_REGISTER_ENVS=false
export CONDA_NO_PLUGINS=true
export CONDA_PKGS_DIRS="$VAPTAMP_ROOT/.runtime/conda-pkgs"
export CONDA_ENVS_PATH="$VAPTAMP_ROOT/.runtime/envs"
export XDG_CACHE_HOME="$VAPTAMP_ROOT/.runtime/cache"
export PIP_CACHE_DIR="$VAPTAMP_ROOT/.runtime/cache/pip"
export TMPDIR="$VAPTAMP_ROOT/.runtime/tmp"
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
# The login shell on this machine exports ROS packages through PYTHONPATH.
# A dedicated Conda prefix does not isolate those inherited search paths.
unset PYTHONPATH PYTHONHOME
mkdir -p "$CONDA_PKGS_DIRS" "$CONDA_ENVS_PATH" "$XDG_CACHE_HOME" "$PIP_CACHE_DIR" "$TMPDIR"
