"""Bounded native OmniGibson startup check, without a task or VLM."""
import os
from pathlib import Path
import sys
import argparse
from datetime import datetime, timezone

root = Path(os.environ["VAPTAMP_ROOT"])
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--original-scene', action='store_true')
args = parser.parse_args()
sys.argv = sys.argv[:1]
runtime = root / ".runtime"
probe_dir = runtime / "probes" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
probe_dir.mkdir(parents=True, exist_ok=False)
print("Probe output:", probe_dir, flush=True)
sys.argv += [
    "--portable", "--portable-root", str(runtime / "kit-portable"),
    "--/app/settings/persistent=false", "--/app/settings/loadUserConfig=false",
    "--/app/extensions/fsWatcherEnabled=false",
    "--/structuredLog/logDirectory=" + str(runtime / "structured-logs"),
    "--/app/tokens/omni_global_cache=" + str(runtime / "cache/omni"),
    "--/app/tokens/omni_global_logs=" + str(runtime / "structured-logs"),
    "--/app/tokens/omni_documents=" + str(runtime / "documents"),
    "--/app/tokens/shared_documents=" + str(runtime / "documents/shared"),
    "--/app/tokens/app_documents=" + str(runtime / "documents/app"),
    "--/app/tokens/documents=" + str(runtime / "documents/app"),
    "--/log/file=" + str(probe_dir / "kit.log"),
]

import omnigibson as og
from omnigibson.macros import gm

gm.HEADLESS = True
try:
    og.launch()
    for _ in range(5):
        og.app.update()
    print("NATIVE_ENGINE_LAUNCH_OK", flush=True)
    if args.original_scene:
        import yaml
        import json
        import numpy as np
        from PIL import Image
        config = yaml.safe_load((Path(og.example_config_path) / 'fetch_behavior.yaml').read_text())
        for robot_config in config['robots']:
            for modality in ('seg_semantic', 'seg_instance'):
                if modality not in robot_config['obs_modalities']:
                    robot_config['obs_modalities'].append(modality)
        config['scene'].update(scene_model='Ihlen_0_int', load_task_relevant_only=True,
                               not_load_object_categories=['ceilings'])
        config['task'] = dict(type='BehaviorTask', activity_name='store_firewood',
                              activity_definition_id=0, activity_instance_id=0,
                              predefined_problem=None, online_object_sampling=False)
        env = og.Environment(configs=config)
        env.reset()
        for _ in range(10):
            og.sim.step()
        robot = env.robots[0]
        obs, info = robot.get_obs()
        summary = dict(kind='environment_probe_only', scene='Ihlen_0_int', task='store_firewood',
                       robot=robot.name, observations={}, object_names=[o.name for o in env.scene.objects])
        for sensor, data in obs.items():
            if isinstance(data, dict):
                summary['observations'][sensor] = {k:list(np.asarray(v).shape) for k,v in data.items()}
                if 'rgb' in data:
                    Image.fromarray(np.asarray(data['rgb'])[..., :3].astype(np.uint8)).save(probe_dir / (sensor + '.png'))
        (probe_dir / 'scene_summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print('ORIGINAL_SCENE_CAMERA_OK', probe_dir, flush=True)
finally:
    og.shutdown()
