"""Collect bounded native stacks without altering host ptrace or driver settings."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from startup_series import processes

root=Path(__file__).resolve().parents[1]
if processes():
    raise SystemExit('Existing simulator process; debugger launch refused')
out=root/'results/original/startup_debug'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out.mkdir(parents=True,exist_ok=False)
env=os.environ.copy();env['VAPTAMP_PROBE_DIR']=str(out/'probe')
command=['gdb','-q','-batch','-ex','set pagination off','-ex','set debuginfod enabled off',
         '-ex','set confirm off','-ex','run','-ex','thread apply all bt 16','-ex','quit',
         '--args',sys.executable,'-u',str(root/'scripts/probe_engine.py')]
print('NATIVE_DEBUG',out,flush=True)
start=time.monotonic()
with (out/'gdb.log').open('w') as log:
    child=subprocess.Popen(command,env=env,cwd=root,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    interrupted=False
    try:child.wait(timeout=75)
    except subprocess.TimeoutExpired:
        interrupted=True
        child.send_signal(signal.SIGINT)
        try:child.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait()
    remnants=processes(child.pid)
    if remnants:
        os.killpg(child.pid,signal.SIGKILL)
        time.sleep(2)
result=dict(exit_code=child.returncode,wall_seconds=time.monotonic()-start,
            interrupted_for_stacks=interrupted,remaining_processes=processes())
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
