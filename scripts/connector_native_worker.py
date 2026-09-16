"""Native worker. Invoke through connector_launch.py for timeout/cleanup."""
import argparse, faulthandler, json, os, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'vlm-tamp'),str(ROOT/'scripts')]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--mode',default='scene')
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
t0=time.monotonic()
def log(event,**data):
    with (a.output/'events.jsonl').open('a') as f:
        f.write(json.dumps(dict(event=event,seconds=time.monotonic()-t0,**data),default=lambda x:x.tolist())+'\n')
    if event in ('scene_loading','scene_ready','completed','failure'):print(event,flush=True)
rt=ROOT/'.runtime';sys.argv=[sys.argv[0],'--portable','--portable-root',str(rt/'kit-portable'),
 '--/app/settings/persistent=false','--/app/settings/loadUserConfig=false','--/app/extensions/fsWatcherEnabled=false',
 '--/log/file='+str(a.output/'kit.log'),'--/structuredLog/logDirectory='+str(rt/'structured-logs')]
for token,sub in {'omni_global_cache':'cache/omni','omni_global_logs':'structured-logs','omni_documents':'documents',
'shared_documents':'documents/shared','app_documents':'documents/app','documents':'documents/app'}.items():
 sys.argv.append('--/app/tokens/'+token+'='+str(rt/sub))
faulthandler.enable();faulthandler.dump_traceback_later(60,repeat=True)
from native_runtime import apply_cpu_affinity
apply_cpu_affinity()
import omnigibson as og
from omnigibson.macros import gm
gm.HEADLESS=True;gm.USE_GPU_DYNAMICS=True
success=False
try:
 from experiments.connector_handoff.scene import ConnectorScene
 scene=ConnectorScene(log)
 from PIL import Image
 third,robot=scene.capture();Image.fromarray(third).save(a.output/'third.png');Image.fromarray(robot).save(a.output/'robot.png')
 if a.mode!='scene':
  from experiments.connector_handoff.validation import run
  run(a.mode,scene,a.output,log)
 log('completed');success=True
except Exception as exc:
 import traceback
 log('failure',error_type=type(exc).__name__,message=str(exc));traceback.print_exc()
finally:
 log('shutdown_started');og.shutdown()
# Kit may exit inside shutdown; parent checks completed marker.
