"""Run one bounded renderer check in the pinned rootfs with host NVIDIA libraries."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time

root = Path(__file__).resolve().parents[1]
fs = root/'.runtime/og-image-rootfs'
assert (fs/'IMAGE_RECEIPT.json').exists()
p = argparse.ArgumentParser()
p.add_argument('--timeout',type=int,default=60)
p.add_argument('--check-only',action='store_true')
p.add_argument('--task', choices=['bringing_water'])
args=p.parse_args()
out=root/'results/original/image_renderer'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out.mkdir(parents=True)
# Driver component selection mirrors NVIDIA runtime injection, without adding host libc.
links=root/'.runtime/og-image-driver-links'
links.mkdir(exist_ok=True)
selected=[]
for pattern in ['libnvidia*.so*','libcuda.so*','libnvoptix.so*','libGLX_nvidia.so*','libEGL_nvidia.so*','libnvcuvid.so*']:
 for f in Path('/usr/lib/x86_64-linux-gnu').glob(pattern):
  target=links/f.name
  if not target.is_symlink():target.symlink_to('/host-driver/'+f.resolve().name)
  selected.append(str(f))
(out/'driver_libraries.json').write_text(json.dumps(sorted(set(selected)),indent=2))
for name in ['image_renderer_smoke.py','native_stage_trace.py']:
 (out/name).write_bytes((root/'scripts'/name).read_bytes())
command=['bwrap','--unshare-user','--uid','0','--gid','0','--die-with-parent','--new-session',
 '--bind',str(fs),'/', '--dev-bind','/dev','/dev','--proc','/proc','--tmpfs','/tmp','--tmpfs','/run',
 '--ro-bind','/sys','/sys','--bind',str(out),'/output',
 '--bind',str(root),'/project',
 '--ro-bind',str(links),'/driver-libs','--ro-bind','/usr/lib/x86_64-linux-gnu','/host-driver',
 '--ro-bind','/usr/share/vulkan/icd.d/nvidia_icd.json','/driver/nvidia_icd.json',
 '--ro-bind','/usr/bin/nvidia-smi','/usr/bin/nvidia-smi',
 '--clearenv','--setenv','PATH','/micromamba/envs/omnigibson/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
 '--setenv','HOME','/root','--setenv','LD_LIBRARY_PATH','/driver-libs',
 '--setenv','VK_ICD_FILENAMES','/driver/nvidia_icd.json',
 '--setenv','PYTHONNOUSERSITE','1','--setenv','PYTHONDONTWRITEBYTECODE','1',
 '--setenv','TMPDIR','/tmp','--setenv','OPTIX_CACHE_PATH','/output/optix',
 '--setenv','CUDA_CACHE_PATH','/output/cuda','--setenv','__GL_SHADER_DISK_CACHE_PATH','/output/gl',
 '--setenv','XDG_CACHE_HOME','/output/cache','--setenv','XDG_CONFIG_HOME','/output/config',
 '--setenv','XDG_DATA_HOME','/output/data','--setenv','XDG_RUNTIME_DIR','/output/run',
 '--setenv','VAPTAMP_ROOT','/project','--setenv','VAPTAMP_PROBE_DIR','/output/probe',
 '--setenv','OMNIGIBSON_ASSET_PATH','/project/.runtime/data/assets',
 '--setenv','OMNIGIBSON_DATASET_PATH','/project/.runtime/data/og_dataset',
 '--setenv','OMNIGIBSON_KEY_PATH','/project/.runtime/data/omnigibson.key',
 '--chdir','/omnigibson-src','--','/bin/bash','-c']
script='source /isaac-sim/setup_conda_env.sh\n'
if args.check_only:
 script += 'cat /etc/os-release\npython --version\nnvidia-smi --query-gpu=name,driver_version --format=csv,noheader\n'
elif args.task:
 script += 'exec python -u /project/scripts/probe_engine.py --task bringing_water --allow-root\n'
else:
 script += 'cp /omnigibson-src/omnigibson/omnigibson.kit /isaac-sim/apps/omnigibson.kit\nexec python -u /output/image_renderer_smoke.py\n'
command.append(script)
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
print('IMAGE_RENDERER',out,flush=True)
start=time.monotonic()
with (out/'console.log').open('w') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 timed_out=False
 try:child.wait(timeout=args.timeout)
 except subprocess.TimeoutExpired:
  timed_out=True
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=3)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 # Kill any descendants remaining in this probe's own process group.
 try:os.killpg(child.pid,signal.SIGKILL)
 except ProcessLookupError:pass
phase_path = out / ('probe/phases.jsonl' if args.task else 'phases.jsonl')
phases=[json.loads(l) for l in phase_path.read_text().splitlines()] if phase_path.exists() else []
events={x['event'] for x in phases}
required = ['camera_ready','shutdown_started'] if args.task else ['hydra_ready','rgb_saved','physics_stepped','shutdown_enter']
result=dict(exit_code=child.returncode,timed_out=timed_out,seconds=time.monotonic()-start,
 success=child.returncode==0 and not timed_out and 'probe_failed' not in events and all(x in events for x in required),check_only=args.check_only,task=args.task)
(out/'summary.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
