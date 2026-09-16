"""Bounded isolated native worker using the existing environment and engine."""
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def launch(mode,output,timeout=150,extra_env=None):
    from native_runtime import apply_cpu_affinity
    apply_cpu_affinity()
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    if not os.getenv('EXP_PATH'):raise RuntimeError('Source scripts/engine_runtime.sh first')
    env=os.environ.copy();env.update(extra_env or {})
    from startup_series import external_snapshot,processes,gpu
    before=external_snapshot();start=time.monotonic();gpu_before=gpu()
    with (output/'terminal.log').open('w') as f:
        child=subprocess.Popen([sys.executable,str(ROOT/'scripts/connector_native_worker.py'),'--mode',mode,'--output',str(output)],
            cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        try:child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        finally:
            if processes(child.pid):os.killpg(child.pid,signal.SIGKILL);time.sleep(1)
    events=[json.loads(x) for x in (output/'events.jsonl').read_text().splitlines()] if (output/'events.jsonl').exists() else []
    after=external_snapshot()
    result=dict(mode=mode,wall_seconds=time.monotonic()-start,exit_code=child.returncode,
        success=any(x['event']=='completed' for x in events),remaining_processes=processes(child.pid),
        external_changes=[k for k in set(before)|set(after) if before.get(k)!=after.get(k)],
        gpu_before_mib=gpu_before,gpu_after_mib=gpu(),baseline_sha='c315720',
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    (output/'run_metadata.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',default='scene');p.add_argument('--output',type=Path,required=True);p.add_argument('--timeout',type=int,default=150)
 a=p.parse_args();raise SystemExit(0 if launch(a.mode,a.output,a.timeout)['success'] else 1)
