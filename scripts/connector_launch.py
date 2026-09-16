"""Bounded isolated native worker using the existing environment and engine."""
import argparse,json,os,signal,subprocess,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def launch(mode,output,timeout=150,extra_env=None):
    from native_runtime import apply_cpu_affinity
    apply_cpu_affinity()
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    if not os.getenv('EXP_PATH'):raise RuntimeError('Source scripts/engine_runtime.sh first')
    env=os.environ.copy();env.update(extra_env or {})
    commit_at_launch=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    working_tree_at_launch=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).splitlines()
    source_dir=output/'source_snapshot';source_dir.mkdir()
    hashes={}
    for source in sorted((ROOT/'experiments/connector_handoff').rglob('*')):
        if source.is_file() and '__pycache__' not in source.parts:
            relative=source.relative_to(ROOT);target=source_dir/relative
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
            hashes[str(relative)]=hashlib.sha256(source.read_bytes()).hexdigest()
    (output/'source_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    from startup_series import external_snapshot,processes,gpu
    timed_out=False
    before=external_snapshot();start=time.monotonic();gpu_before=gpu()
    with (output/'terminal.log').open('w') as f:
        child=subprocess.Popen([sys.executable,str(ROOT/'scripts/connector_native_worker.py'),'--mode',mode,'--output',str(output)],
            cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
        try:child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        finally:
            if processes(child.pid):os.killpg(child.pid,signal.SIGKILL);time.sleep(1)
    events=[json.loads(x) for x in (output/'events.jsonl').read_text().splitlines()] if (output/'events.jsonl').exists() else []
    if mode in ('live','mock_straight','mock_replan') and not (output/'episode/episode.json').exists():
        episode=output/'episode';episode.mkdir(exist_ok=True)
        trace=episode/'events.jsonl';rows=[json.loads(x) for x in trace.read_text().splitlines()] if trace.exists() else []
        first=next((x for x in rows if x['event']=='episode_start'),{})
        boundary='LIVE' if mode=='live' else 'MOCK'
        meta=dict(mode=boundary,label=boundary if boundary=='LIVE' else 'NON-SCIENTIFIC MOCK VLM RUN',
            seed=int(env.get('CONNECTOR_SEED','0')),evaluation_only={'scene_condition':env.get('CONNECTOR_CONDITION')},
            physical_success=False,infrastructure_error=True,error_type='WorkerTimeout' if timed_out else 'WorkerFailure')
        if not first:
            rows.append(dict(meta,event='episode_start',sequence=0,seconds=0,frame_index=0))
        rows.append(dict(meta,event='episode_end',sequence=len(rows),seconds=rows[-1]['seconds'],frame_index=rows[-1].get('frame_index',0)))
        trace.write_text(''.join(json.dumps(x)+'\n' for x in rows))
        (episode/'episode.json').write_text(json.dumps(meta,indent=2)+'\n')
    after=external_snapshot()
    result=dict(mode=mode,wall_seconds=time.monotonic()-start,exit_code=child.returncode,
        timed_out=timed_out,success=any(x['event']=='completed' for x in events),remaining_processes=processes(child.pid),
        external_changes=[k for k in set(before)|set(after) if before.get(k)!=after.get(k)],
        gpu_before_mib=gpu_before,gpu_after_mib=gpu(),baseline_sha='c315720',
        working_tree=working_tree_at_launch,
        configuration={k:v for k,v in (extra_env or env).items() if k in ('CONNECTOR_SEED','CONNECTOR_CONDITION','CONNECTOR_REPEATS','VAPTAMP_VLM_PROVIDER','VAPTAMP_GEMINI_MODEL')},
        commit=commit_at_launch)
    (output/'run_metadata.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
    return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',default='scene');p.add_argument('--output',type=Path,required=True);p.add_argument('--timeout',type=int,default=150)
 a=p.parse_args();raise SystemExit(0 if launch(a.mode,a.output,a.timeout)['success'] else 1)
