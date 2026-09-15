#!/usr/bin/env bash
# Diagnostic: use the extracted engine's own Python and library setup.
source "$(dirname -- "${BASH_SOURCE[0]}")/engine_runtime.sh"
unset CONDA_PREFIX PYTHONPATH LD_LIBRARY_PATH PYTHONEXE
source "$VAPTAMP_ROOT/.runtime/native/isaac-sim/setup_python_env.sh"
export LD_PRELOAD="$VAPTAMP_ROOT/.runtime/native/isaac-sim/kit/libcarb.so"
