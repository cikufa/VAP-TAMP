"""Shared task CLI launch; no environment installation or host mutation."""
import os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def native(mode,output,timeout=600,extra=None):
    env=os.environ.copy();env.update({k:str(v) for k,v in (extra or {}).items()})
    command=['bash','-c','source scripts/engine_runtime.sh && exec python scripts/connector_launch.py "$@"',
             'connector','--mode',mode,'--output',str(Path(output).resolve()),'--timeout',str(timeout)]
    return subprocess.run(command,cwd=ROOT,env=env).returncode

def validation_cli(mode):
    import argparse,datetime
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);p.add_argument('--repeats',type=int,default=5)
    p.add_argument('--timeout',type=int,default=900);a=p.parse_args()
    output=a.output or ROOT/'results/custom_connector/benchmark_validation'/mode/datetime.datetime.now().strftime('%Y%m%dT%H%M%S')
    code=native(mode,output,a.timeout,{'CONNECTOR_REPEATS':a.repeats})
    if code==0 and mode in ('physics_validation','grasp_validation'):
        import shutil
        destination='physics_validation.csv' if mode=='physics_validation' else 'grasp_validation.csv'
        shutil.copyfile(output/'physics_validation.csv',ROOT/'results/custom_connector'/destination)
        sys.path.insert(0,str(ROOT))
        from experiments.connector_handoff.media import render_all
        for episode in sorted(output.glob('00_*')):render_all(episode)
    raise SystemExit(code)
