"""Sequential, bounded native probes with phase, GPU and cleanup evidence."""
import argparse
import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]

def gpu():
    return subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'], text=True).strip()

def gpu_processes():
    return subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory',
                                    '--format=csv,noheader'],text=True).strip()

def processes(group=None):
    found=[]
    for p in Path('/proc').glob('[0-9]*'):
        try:
            stat=(p/'stat').read_text().rsplit(')',1)[1].split()
            cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
            if (group is not None and int(stat[2])==group) or (group is None and any(x in cmd for x in ('probe_engine.py','isaac-sim/kit/kit'))):
                found.append(dict(pid=int(p.name), state=stat[0], command=cmd))
        except (OSError,ValueError):
            pass
    return found

def external_snapshot():
    result={}
    for relative in ('.nvidia-omniverse','.cache/ov','.local/share/ov','Documents/Kit','Documents/Omniverse'):
        base=Path.home()/relative
        if base.exists():
            for p in base.rglob('*'):
                if p.is_file():
                    s=p.stat();result[str(p)]=[s.st_size,s.st_mtime_ns]
    return result

def main():
    from native_runtime import apply_cpu_affinity
    apply_cpu_affinity()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--count',type=int,default=5)
    parser.add_argument('--timeout',type=int,default=120)
    parser.add_argument('--task',choices=['bringing_water','halve_an_egg'])
    parser.add_argument('--cache-root',type=Path)
    args=parser.parse_args()
    out=ROOT/'results/original/startup'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True,exist_ok=False)
    probe_source=(ROOT/'scripts/probe_engine.py').read_bytes()
    probe_copy=out/'probe_engine.py'
    probe_copy.write_bytes(probe_source)
    (out/'native_stage_trace.py').write_bytes((ROOT/'scripts/native_stage_trace.py').read_bytes())
    (out/'task_load_trace.py').write_bytes((ROOT/'scripts/task_load_trace.py').read_bytes())
    for relative in ('scripts/released_actions_smoke.py', 'vlm-tamp/fetch_camera_compat.py', 'vlm-tamp/primitive_compat.py', 'vlm-tamp/eval.py',
                     'scripts/paper_adapter_smoke.py', 'vlm-tamp/paper_sim_adapter.py',
                     'vlm-tamp/paper_verification.py', 'vlm-tamp/vlm_backends.py', 'vlm-tamp/gpt4v.py'):
        (out/Path(relative).name).write_bytes((ROOT/relative).read_bytes())
    source_sha256=hashlib.sha256(probe_source).hexdigest()
    print('STARTUP_SERIES',out,flush=True)
    reports=[]
    for i in range(args.count):
        stale=processes()
        if stale:
            raise RuntimeError('Existing simulator probe processes; refusing concurrent launch: '+str(stale))
        folder=out/f'probe_{i+1}'
        env=os.environ.copy();env['VAPTAMP_PROBE_DIR']=str(folder)
        if args.cache_root:
            cache_root=(ROOT/args.cache_root).resolve()
            if not cache_root.is_relative_to(ROOT):raise ValueError('Cache must remain project-local')
            env['VAPTAMP_PROBE_CACHE_ROOT']=str(cache_root)
        before=external_snapshot()
        report=dict(index=i+1,launch_utc=datetime.now(timezone.utc).isoformat(),gpu_before_mib=gpu(),gpu_processes_before=gpu_processes(),gpu_samples=[],task=args.task)
        report['probe_source_sha256']=source_sha256
        report['diagnostic_environment']={k:v for k,v in env.items() if k.startswith('VAPTAMP_NATIVE_') or k in ('VAPTAMP_MINIMAL_SCENE', 'VAPTAMP_SCENE_MODEL')}
        report['cache_root']=env.get('VAPTAMP_PROBE_CACHE_ROOT','existing project cache')
        report['omp_num_threads']=env.get('OMP_NUM_THREADS','unset')
        report['diagnostic_async_loads']=env.get('VAPTAMP_PROBE_ASYNC_LOADS')=='1'
        report['preload_torch']=env.get('VAPTAMP_PROBE_PRELOAD_TORCH')=='1'
        report['released_lookat_requested']=env.get('VAPTAMP_PROBE_LOOKAT')=='1'
        report['released_actions_requested']=env.get('VAPTAMP_PROBE_ACTIONS')=='1'
        report['moved_object_probe_requested']=bool(env.get('VAPTAMP_PROBE_MOVED_OBJECT'))
        report['paper_adapter_probe_requested']=env.get('VAPTAMP_PROBE_PAPER_AP')=='1'
        report['paper_collision_probe_requested']=env.get('VAPTAMP_PROBE_PAPER_COLLISION')=='1'
        command=[sys.executable,'-u',str(probe_copy)]
        if args.task:command += ['--task',args.task]
        if env.get('VAPTAMP_NATIVE_STRACE') == '1':
            command = ['strace', '-f', '-tt', '-T', '-e', 'trace=%file,%network', '-o', str(out/f'probe_{i+1}.strace')] + command
        with (out/f'probe_{i+1}.log').open('w') as log:
            child=subprocess.Popen(command,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            start=time.monotonic();timed_out=False
            while child.poll() is None:
                report['gpu_samples'].append(dict(seconds=time.monotonic()-start,mib=gpu()))
                if time.monotonic()-start>args.timeout:
                    timed_out=True
                    os.killpg(child.pid,signal.SIGTERM)
                    try:child.wait(timeout=5)
                    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL)
                    child.wait();break
                time.sleep(2)
        remnants=processes(child.pid)
        if remnants:
            os.killpg(child.pid,signal.SIGKILL)
            time.sleep(1)
        time.sleep(2)
        report.update(exit_code=child.returncode,timed_out=timed_out,wall_seconds=time.monotonic()-start,
                      gpu_after_mib=gpu(),remaining_group_processes=processes(child.pid),remaining_simulator_processes=processes(),
                      gpu_processes_after=gpu_processes(),
                      terminal_log=str(out/f'probe_{i+1}.log'),kit_log=str(folder/'kit.log'))
        phases=[json.loads(line) for line in (folder/'phases.jsonl').read_text().splitlines()] if (folder/'phases.jsonl').exists() else []
        phase={p['event']:p['elapsed_seconds'] for p in phases}
        report['phases']=phases
        report['initialization_seconds']=(phase['engine_initialized']-phase['engine_initializing']) if 'engine_initialized' in phase else None
        report['process_to_engine_ready_seconds']=phase.get('engine_initialized')
        report['scene_load_seconds']=phase.get('scene_loaded',0)-phase['scene_loading'] if 'scene_loaded' in phase else None
        report['scene_status']='not_requested' if not args.task else ('loaded' if 'scene_loaded' in phase else 'not_reached_or_failed')
        terminal_text=(out/f'probe_{i+1}.log').read_text(errors='replace')
        # Isaac 2023.1.1 defaults to fast_shutdown=True: close() exits the process.
        # The parent must observe exit status; code following close() need not run.
        report['shutdown_observed'] = child.returncode == 0 and not timed_out and 'shutdown_started' in phase and ('shutdown_completed' in phase or 'Simulation App Shutting Down' in terminal_text)
        report['success']=report['shutdown_observed'] and 'probe_failed' not in phase and (not args.task or 'camera_ready' in phase)
        if report['released_lookat_requested']:
            report['success'] = report['success'] and 'primitive_completed' in phase
        if report['released_actions_requested']:
            report['success'] = report['success'] and 'scripted_plan_completed' in phase
        if report['moved_object_probe_requested']:
            report['success'] = report['success'] and 'moved_object_probe_completed' in phase
        if report['paper_adapter_probe_requested'] and not report['paper_collision_probe_requested']:
            report['success'] = report['success'] and 'paper_adapter_probe_completed' in phase
        if report['paper_collision_probe_requested']:
            report['success'] = report['success'] and 'paper_collision_probe_completed' in phase
        if env.get('VAPTAMP_MINIMAL_SCENE') == '1' or env.get('VAPTAMP_SCENE_MODEL'):
            report['success'] = report['success'] and 'minimal_rgb_saved' in phase
        if env.get('VAPTAMP_NATIVE_WITHOUT_OG') == '1':
            report['success'] = report['success'] and all(name in phase for name in ('native_rgb_saved', 'native_physics_stepped'))
        report['native_trace_sha256']=hashlib.sha256((out/'native_stage_trace.py').read_bytes()).hexdigest()
        after=external_snapshot()
        report['external_file_changes']=[p for p in set(before)|set(after) if before.get(p)!=after.get(p)]
        reports.append(report)
        (out/'summary.json').write_text(json.dumps(reports,indent=2)+'\n')
        print('PROBE_RESULT',i+1,report['success'],report['wall_seconds'],'GPU',report['gpu_before_mib'],report['gpu_after_mib'],'external_changes',len(report['external_file_changes']),flush=True)
        if report['remaining_group_processes'] or report['remaining_simulator_processes'] or report['external_file_changes']:
            raise RuntimeError('Cleanup or containment failure; series stopped')
        if not report['success']:
            raise SystemExit('Probe failed; series stopped for diagnosis instead of repeating the same attempt')

if __name__=='__main__':main()
