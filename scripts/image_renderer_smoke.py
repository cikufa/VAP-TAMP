"""Minimal RTX RGB/physics acceptance inside the isolated official userspace image."""
import faulthandler
import json
import os
from pathlib import Path
import sys
import time
out = Path('/output')
start = time.monotonic()
def event(name, **fields):
    line = json.dumps(dict(event=name, seconds=time.monotonic()-start, **fields))
    print('PHASE', line, flush=True)
    with (out/'phases.jsonl').open('a') as f: f.write(line+'\n')
faulthandler.enable()
faulthandler.dump_traceback_later(30, repeat=True)
sys.argv += ['--allow-root', '--portable', '--portable-root', '/output/portable',
 '--/app/settings/persistent=false', '--/app/settings/loadUserConfig=false',
 '--/app/extensions/fsWatcherEnabled=false', '--/structuredLog/logDirectory=/output/logs',
 '--/app/tokens/omni_global_cache=/output/cache', '--/app/tokens/omni_global_logs=/output/logs',
 '--/app/tokens/omni_documents=/output/documents', '--/app/tokens/shared_documents=/output/documents',
 '--/app/tokens/app_documents=/output/documents', '--/app/tokens/documents=/output/documents',
 '--/log/file=/output/kit.log']
from native_stage_trace import install
install(event)
from omni.isaac.kit import SimulationApp
event('python', executable=sys.executable, version=sys.version)
app = SimulationApp({'headless':True,'multi_gpu':False,'active_gpu':0,'physics_gpu':0},
 experience='/isaac-sim/apps/omnigibson.kit')
event('hydra_ready')
try:
 import numpy as np
 import omni.replicator.core as rep
 render_product = rep.create.render_product('/OmniverseKit_Persp', (64,64))
 rgb = rep.AnnotatorRegistry.get_annotator('rgb')
 rgb.attach([render_product])
 for _ in range(10):app.update()
 rep.orchestrator.step(rt_subframes=4)
 pixels = np.asarray(rgb.get_data())
 assert pixels.ndim == 3 and pixels.shape[:2] == (64,64), pixels.shape
 np.save(out/'rgb.npy', pixels[...,:3])
 event('rgb_saved',shape=list(pixels[...,:3].shape))
 from omni.isaac.core import SimulationContext
 sim = SimulationContext()
 sim.initialize_physics()
 sim.play()
 sim.step(render=True)
 assert sim.current_time > 0
 event('physics_stepped',simulation_time=sim.current_time)
 sim.stop()
finally:
 event('shutdown_enter')
 app.close()
 event('shutdown_exit')
faulthandler.cancel_dump_traceback_later()
