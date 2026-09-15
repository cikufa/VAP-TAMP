#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/project_runtime.sh"
cd "$VAPTAMP_ROOT"
VAPTAMP_PYTHON="$VAPTAMP_ROOT/.runtime/envs/vaptamp-repro/bin/python"
VAPTAMP_CONDA="${VAPTAMP_CONDA_EXE:-/home/shekoufeh/miniconda3/bin/conda}"
"$VAPTAMP_CONDA" env export --prefix "$VAPTAMP_ROOT/.runtime/envs/vaptamp-repro" > environment.yml
"$VAPTAMP_CONDA" list --prefix "$VAPTAMP_ROOT/.runtime/envs/vaptamp-repro" --explicit > conda_explicit.txt
"$VAPTAMP_PYTHON" -m pip list --format=freeze > requirements_frozen.txt
{
    echo '# Installed environment versions'
    echo
    echo 'Environment provisioning is incomplete until native startup and the original scene pass.'
    echo 'See original_reproduction_status.md for episode status; this is not a reproduced-baseline claim.'
    echo 'Inherited ROS PYTHONPATH and user-site imports are disabled during export.'
    echo 'The engine is external to Conda at .runtime/native/isaac-sim, within this project.'
    echo
    echo '```text'
    "$VAPTAMP_PYTHON" --version
    "$VAPTAMP_PYTHON" -m pip --version
    "$VAPTAMP_CONDA" list --prefix "$VAPTAMP_ROOT/.runtime/envs/vaptamp-repro"
    /usr/bin/cmake --version
    /usr/bin/g++ --version
    nvidia-smi
    echo '```'
    echo
    echo '## Dependency metadata check'
    echo
    echo '```text'
    if "$VAPTAMP_PYTHON" -m pip check; then
        echo 'exit_code=0'
    else
        echo "exit_code=$?"
    fi
    echo '```'
    echo
    echo 'Rtree 1.2.0 has a malformed WHEEL header: its tags follow a blank line.'
    echo 'The recorded manylinux tags intersect this machine’s supported tags, and a native index insertion/intersection query passed.'
    echo 'This warning remains disclosed; metadata was not edited to force a passing check.'
} | sed 's/[[:blank:]]*$//' > docs/environment_versions.md
