# Installed environment versions

Planner-only environment. No simulator, GPU torch or assets installed.
Inherited ROS PYTHONPATH is cleared by scripts/project_runtime.sh.
requirements_frozen.txt uses pip list --format=freeze to record Conda package versions without build-machine file URLs.

```text
Python 3.10.21
pip 26.2.1 from /home/shekoufeh/VAP_TAMP/VAP-TAMP-clean/.runtime/envs/vaptamp-repro/lib/python3.10/site-packages/pip (python 3.10)
# packages in environment at /home/shekoufeh/VAP_TAMP/VAP-TAMP-clean/.runtime/envs/vaptamp-repro:
#
# Name                     Version          Build                 Channel
_openmp_mutex              4.5              20_gnu                conda-forge
bzip2                      1.0.8            hda65f42_10           conda-forge
ca-certificates            2026.7.22        hbd8a1cb_0            conda-forge
click                      8.5.0            pypi_0                pypi
lark                       1.1.9            pypi_0                pypi
ld_impl_linux-64           2.46.1           default_hbd61a6d_102  conda-forge
libexpat                   2.8.1            hecca717_1            conda-forge
libffi                     3.7.0            h81df57d_1            conda-forge
libgcc                     16.2.0           ha9f2e26_5            conda-forge
libgomp                    16.2.0           he0feb66_5            conda-forge
liblzma                    5.8.3            hb03c661_1            conda-forge
libnsl                     2.0.1            hb9d3cd8_1            conda-forge
libsqlite                  3.53.4           h0737f62_1            conda-forge
libuuid                    2.42.3           hcfc3c73_0            conda-forge
libxcrypt                  4.4.38           h280c20c_0            conda-forge
libzlib                    1.3.2            h25fd6f3_3            conda-forge
ncurses                    6.6              hdb14827_1            conda-forge
openssl                    3.6.4            h781a0a9_0            conda-forge
packaging                  26.3             pyhc364b38_0          conda-forge
pddl                       0.4.2            pypi_0                pypi
pip                        26.2.1           pyh8b19718_0          conda-forge
python                     3.10.21          h267e890_0_cpython    conda-forge
readline                   8.3              hd6e31c0_1            conda-forge
setuptools                 84.0.0           pyh332efcf_0          conda-forge
tk                         8.6.13           noxft_h1df4ec4_4      conda-forge
tzdata                     2026c            h151e31d_0            conda-forge
wheel                      0.48.0           pyhd8ed1ab_0          conda-forge
zstd                       1.5.7            hb78ec9c_7            conda-forge
cmake version 3.22.1

CMake suite maintained and supported by Kitware (kitware.com/cmake).
g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
Copyright (C) 2021 Free Software Foundation, Inc.
This is free software; see the source for copying conditions.  There is NO
warranty; not even for MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

Tue Sep 15 12:55:01 2026       
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.105.08             Driver Version: 580.105.08     CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|                                         |                        |               MIG M. |
|=========================================+========================+======================|
|   0  NVIDIA GeForce RTX 4090        On  |   00000000:01:00.0  On |                  Off |
|  0%   47C    P8             32W /  450W |    1945MiB /  24564MiB |     42%      Default |
|                                         |                        |                  N/A |
+-----------------------------------------+------------------------+----------------------+

+-----------------------------------------------------------------------------------------+
| Processes:                                                                              |
|  GPU   GI   CI              PID   Type   Process name                        GPU Memory |
|        ID   ID                                                               Usage      |
|=========================================================================================|
|    0   N/A  N/A            2581      G   /usr/lib/xorg/Xorg                      660MiB |
|    0   N/A  N/A            6201      G   /usr/bin/gnome-shell                    254MiB |
|    0   N/A  N/A            8244      G   ...bin/snapd-desktop-integration         60MiB |
|    0   N/A  N/A         1464026      G   /opt/zotero/zotero-bin                   16MiB |
|    0   N/A  N/A         2881935      G   .../8863/usr/lib/firefox/firefox        444MiB |
|    0   N/A  N/A         3057533      G   ...rack-uuid=3190708988185955192        108MiB |
|    0   N/A  N/A         3538852      G   gnome-control-center                     92MiB |
|    0   N/A  N/A         3738644      G   ...rack-uuid=3190708988185955192         33MiB |
+-----------------------------------------------------------------------------------------+
```
