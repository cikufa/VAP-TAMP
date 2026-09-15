#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/project_runtime.sh"
cd "$VAPTAMP_ROOT"
# Existing Ubuntu CMake is used; no system package installation.
/usr/bin/cmake -S vlm-tamp/downward/src -B vlm-tamp/downward/builds/release -DCMAKE_BUILD_TYPE=Release
/usr/bin/cmake --build vlm-tamp/downward/builds/release -j "${VAPTAMP_BUILD_JOBS:-6}"
/usr/bin/cmake -S vlm-tamp/VAL -B vlm-tamp/VAL/build/linux64/Release -DCMAKE_BUILD_TYPE=Release
/usr/bin/cmake --build vlm-tamp/VAL/build/linux64/Release -j "${VAPTAMP_BUILD_JOBS:-6}"
