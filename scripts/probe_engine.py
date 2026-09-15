"""Bounded native OmniGibson startup check, without a task or VLM."""
import os
from pathlib import Path
import sys
import argparse
import time
import json
import faulthandler
from datetime import datetime, timezone

root = Path(os.environ["VAPTAMP_ROOT"])
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--original-scene', action='store_true')
parser.add_argument('--task', choices=['bringing_water', 'halve_an_egg'])
parser.add_argument('--allow-root', action='store_true', help='For the isolated user namespace only')
args = parser.parse_args()
sys.argv = sys.argv[:1]
if args.allow_root:
    sys.argv.append('--allow-root')
runtime = root / ".runtime"
probe_dir = Path(os.environ.get('VAPTAMP_PROBE_DIR', runtime / "probes" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")))
probe_dir.mkdir(parents=True, exist_ok=False)
print("Probe output:", probe_dir, flush=True)
started = time.monotonic()
def event(name, **fields):
    with (probe_dir / 'phases.jsonl').open('a') as output:
        output.write(json.dumps(dict(event=name, elapsed_seconds=time.monotonic()-started, **fields))+'\n')
event('process_started', python_executable=sys.executable, python_version=sys.version,
      cpu_affinity=sorted(os.sched_getaffinity(0)))
cache_root=Path(os.environ.get('VAPTAMP_PROBE_CACHE_ROOT',runtime/'cache'))
portable_root=runtime/'kit-portable'
if 'VAPTAMP_PROBE_CACHE_ROOT' in os.environ:
    if not cache_root.resolve().is_relative_to(root):raise ValueError('Cache must remain project-local')
    portable_root=cache_root/'kit-portable'
    for key,subdir in [('XDG_CACHE_HOME','xdg'),('CUDA_CACHE_PATH','cuda'),('__GL_SHADER_DISK_CACHE_PATH','nvidia')]:
        os.environ[key]=str(cache_root/subdir)
        (cache_root/subdir).mkdir(parents=True,exist_ok=True)
faulthandler.enable()
faulthandler.dump_traceback_later(60, repeat=True)
sys.argv += [
    "--portable", "--portable-root", str(portable_root),
    "--/app/settings/persistent=false", "--/app/settings/loadUserConfig=false",
    "--/app/extensions/fsWatcherEnabled=" + ("true" if os.getenv("VAPTAMP_NATIVE_WATCHERS") == "1" else "false"),
    "--/structuredLog/logDirectory=" + str(runtime / "structured-logs"),
    "--/app/tokens/omni_global_cache=" + str(cache_root / "omni"),
    "--/app/tokens/omni_global_logs=" + str(runtime / "structured-logs"),
    "--/app/tokens/omni_documents=" + str(runtime / "documents"),
    "--/app/tokens/shared_documents=" + str(runtime / "documents/shared"),
    "--/app/tokens/app_documents=" + str(runtime / "documents/app"),
    "--/app/tokens/documents=" + str(runtime / "documents/app"),
    "--/log/file=" + str(probe_dir / "kit.log"),
]
if os.getenv('VAPTAMP_PROBE_ASYNC_LOADS') == '1':
    # Diagnostic only; never enabled by the baseline launcher.
    sys.argv += ['--/rtx/materialDb/syncLoads=false',
                 '--/rtx/hydra/materialSyncLoads=false',
                 '--/omni.kit.plugin/syncUsdLoads=false']
    event('diagnostic_async_loads_requested')

if os.getenv('VAPTAMP_NATIVE_TASK_THREADS'):
    sys.argv.append('--/plugins/carb.tasking.plugin/threadCount=' + str(int(os.environ['VAPTAMP_NATIVE_TASK_THREADS'])))

# Isolate OG imports from native renderer initialization using the same engine/kit.
if os.getenv('VAPTAMP_NATIVE_WITHOUT_OG') == '1':
    sys.path.append(str(root / 'scripts'))
    from native_stage_trace import install
    install(event)
    from omni.isaac.kit import SimulationApp
    event('native_without_og_enter')
    app = SimulationApp({'headless': True, 'multi_gpu': False,
                         'active_gpu': 0, 'physics_gpu': 0},
                        experience=str(runtime / 'native/isaac-sim/apps/omnigibson.kit'))
    event('native_without_og_ready')
    try:
        import omni.replicator.core as rep
        import numpy as np
        product = rep.create.render_product('/OmniverseKit_Persp', (64, 64))
        rgb_annotator = rep.AnnotatorRegistry.get_annotator('rgb')
        rgb_annotator.attach([product])
        for _ in range(10):
            app.update()
        rep.orchestrator.step(rt_subframes=4)
        rgb = np.asarray(rgb_annotator.get_data())
        assert rgb.ndim == 3 and rgb.shape[:2] == (64, 64) and rgb.shape[2] >= 3, rgb.shape
        rgb = rgb[..., :3]
        assert np.isfinite(rgb).all()
        np.save(probe_dir / 'native_rgb.npy', rgb)
        event('native_rgb_saved', shape=list(rgb.shape))
        from omni.isaac.core import SimulationContext
        context = SimulationContext()
        context.initialize_physics()
        context.play()
        context.step(render=True)
        assert context.current_time > 0
        event('native_physics_stepped', time=context.current_time)
        context.stop()
    finally:
        event('shutdown_started')
        app.close()
        event('shutdown_completed')
    sys.exit(0)

import omnigibson as og
from omnigibson.macros import gm

gm.HEADLESS = True
if args.original_scene or args.task:
    gm.USE_GPU_DYNAMICS = True
if os.getenv('VAPTAMP_PROBE_PRELOAD_TORCH') == '1':
    # eval.py imports gpt4v/torchvision before creating its OG Environment.
    import torch
    import torchvision
    event('ml_dependencies_preloaded',torch_version=torch.__version__,torch_file=torch.__file__)
try:
    if os.getenv('VAPTAMP_NATIVE_TRACE') == '1':
        sys.path.append(str(root / 'scripts'))
        from native_stage_trace import install
        install(event)
    event('engine_initializing')
    og.launch()
    for _ in range(5):
        og.app.update()
    print("NATIVE_ENGINE_LAUNCH_OK", flush=True)
    event('engine_initialized')
    if os.getenv('VAPTAMP_TASK_LOAD_TRACE') == '1':
        sys.path.append(str(root / 'scripts'))
        from task_load_trace import install
        install(event)
    if args.original_scene or args.task:
        import yaml
        import json
        import numpy as np
        from PIL import Image
        config = yaml.safe_load((Path(og.example_config_path) / 'fetch_behavior.yaml').read_text())
        for robot_config in config['robots']:
            for modality in ('seg_semantic', 'seg_instance'):
                if modality not in robot_config['obs_modalities']:
                    robot_config['obs_modalities'].append(modality)
        task = args.task or 'store_firewood'
        scene = {'store_firewood':'Ihlen_0_int', 'bringing_water':'Wainscott_0_garden', 'halve_an_egg':'Rs_int'}[task]
        config['scene'].update(scene_model=scene, load_task_relevant_only=True,
                               not_load_object_categories=['ceilings'])
        config['task'] = dict(type='BehaviorTask', activity_name=task,
                              activity_definition_id=0, activity_instance_id=0,
                              predefined_problem=None, online_object_sampling=False)
        event('scene_loading', task=task, scene=scene)
        env = og.Environment(configs=config)
        event('scene_loaded')
        for modality in ('seg_semantic','seg_instance'):
            env.robots[0].add_obs_modality(modality)
        env.load_observation_space()
        event('camera_warmup_started')
        for _ in range(10):
            og.sim.render()
        event('camera_warmup_completed')
        env.reset()
        for _ in range(10):
            og.sim.step()
        robot = env.robots[0]
        event('robot_head_metadata', joints={name: dict(lower=float(joint.lower_limit), upper=float(joint.upper_limit))
              for name, joint in robot.joints.items() if 'head' in name},
              camera_control_idx=robot.camera_control_idx.tolist(),
              head_links=[name for name in robot.links if 'head' in name or 'eye' in name])
        obs, info = robot.get_obs()
        summary = dict(kind='environment_probe_only', scene=scene, task=task,
                       robot=robot.name, observations={}, object_names=[o.name for o in env.scene.objects])
        for sensor, data in obs.items():
            if isinstance(data, dict):
                summary['observations'][sensor] = {k:list(np.asarray(v).shape) for k,v in data.items()}
                if 'rgb' in data:
                    for modality in ('rgb', 'seg_semantic', 'seg_instance'):
                        frame = np.asarray(data[modality])
                        assert frame.size and np.isfinite(frame).all(), (sensor, modality, frame.shape)
                    Image.fromarray(np.asarray(data['rgb'])[..., :3].astype(np.uint8)).save(probe_dir / (sensor + '.png'))
        (probe_dir / 'scene_summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        print('ORIGINAL_SCENE_CAMERA_OK', probe_dir, flush=True)
        event('camera_ready')
        if os.getenv('VAPTAMP_PROBE_LOOKAT') == '1':
            # Execute the released function unchanged, without eval.py's
            # module-level VLM client or episode loop. This is a motion smoke
            # test, not active perception or manipulation acceptance.
            import ast
            import hashlib
            from omnigibson.action_primitives.starter_semantic_action_primitives import StarterSemanticActionPrimitives
            source = (root / 'vlm-tamp/eval.py').read_text()
            sys.path.insert(0, str(root / 'vlm-tamp'))
            from fetch_camera_compat import look_at_fetch, camera_sensor, pose
            initial_joints = robot.get_joint_positions().copy()
            sensor = camera_sensor(robot)
            # Validate physical axis signs with a reachable target offset from
            # the current optical axis, independent of where task objects lie.
            cp, cr = pose(sensor)
            calibration_target = cp + cr @ np.array([0.5, 0.2, -3.0])
            calibration = look_at_fetch(robot, calibration_target)
            for _ in range(10):
                og.sim.render()
            cp_after, cr_after = pose(sensor)
            actual_direction = cr_after.T @ (calibration_target - cp_after)
            actual_direction /= np.linalg.norm(actual_direction)
            angular_error = float(np.degrees(np.arccos(np.clip(-actual_direction[2], -1, 1))))
            event('head_kinematics_checked', angular_error_degrees=angular_error,
                  solver=calibration, joints_actual=robot.get_joint_positions().tolist(),
                  camera_before=cp.tolist(), camera_after=cp_after.tolist())
            assert angular_error < 2.0, angular_error
            moved = robot.get_joint_positions().copy()
            other_indices = [i for i in range(len(moved)) if i not in robot.camera_control_idx]
            assert np.allclose(initial_joints[other_indices], moved[other_indices], atol=1e-5)
            robot.set_joint_positions(initial_joints)
            pose(sensor)
            for _ in range(3):
                og.sim.render()
            node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'lookat')
            namespace = dict(env=env, robot=robot, ap=StarterSemanticActionPrimitives(env), record=event)
            exec(compile(ast.Module(body=[node], type_ignores=[]), 'released_eval_lookat', 'exec'), namespace)
            target = 'water_bottle.n.01_1'
            before = robot.get_joint_positions().copy()
            event('primitive_started', primitive='released_lookat', target=target,
                  target_position=env.task.object_scope[target].get_position().tolist(),
                  function_sha256=hashlib.sha256(ast.get_source_segment(source, node).encode()).hexdigest())
            namespace['lookat'](target)
            after = robot.get_joint_positions().copy()
            assert np.linalg.norm(after - before) > 1e-6, 'Head joints did not move'
            for _ in range(10):
                og.sim.render()
            moved_obs, _ = robot.get_obs()
            for sensor, data in moved_obs.items():
                if isinstance(data, dict) and 'rgb' in data:
                    Image.fromarray(np.asarray(data['rgb'])[..., :3].astype(np.uint8)).save(probe_dir / (sensor + '_after_lookat.png'))
            event('primitive_completed', joints_before=before.tolist(), joints_after=after.tolist())
        if os.getenv('VAPTAMP_PROBE_ACTIONS') == '1':
            sys.path.insert(0, str(root / 'scripts'))
            from released_actions_smoke import run
            run(root, probe_dir, env, event)
    elif os.getenv('VAPTAMP_MINIMAL_SCENE') == '1' or os.getenv('VAPTAMP_SCENE_MODEL'):
        import numpy as np
        from PIL import Image
        event('minimal_scene_loading')
        minimal_config = {
            'scene': {'type': 'Scene', 'use_skybox': False},
            'objects': [{'type': 'PrimitiveObject', 'name': 'smoke_cube',
                         'primitive_type': 'Cube', 'size': 0.3,
                         'position': [0, 0, 0.5], 'rgba': [1, 0, 0, 1]}],
            'robots': [],
        }
        if os.getenv('VAPTAMP_SCENE_MODEL'):
            minimal_config['scene'] = dict(type='InteractiveTraversableScene', scene_model=os.environ['VAPTAMP_SCENE_MODEL'], load_object_categories=['floors','walls'])
            minimal_config['objects'] = []
            event('behavior_scene_requested', config=minimal_config)
        env = og.Environment(configs=minimal_config)
        event('minimal_scene_loaded', objects=[obj.name for obj in env.scene.objects])
        env.reset()
        for index in range(10):
            event('simulation_step_enter', index=index)
            og.sim.step()
            event('simulation_step_exit', index=index)
        event('rgb_capture_enter')
        obs, _ = og.sim.viewer_camera.get_obs()
        rgb = np.asarray(obs['rgb'])[..., :3]
        assert rgb.ndim == 3 and rgb.shape[2] == 3 and np.isfinite(rgb).all()
        Image.fromarray(rgb.astype(np.uint8)).save(probe_dir / 'minimal_rgb.png')
        event('minimal_rgb_saved', shape=list(rgb.shape), pixel_std=float(rgb.std()))
    else:
        event('scene_not_requested', reason='engine-only stability probe')
except BaseException:
    import traceback
    event('probe_failed', traceback=traceback.format_exc())
    traceback.print_exc()
    raise
finally:
    event('shutdown_started')
    og.shutdown()
    event('shutdown_completed')
    faulthandler.cancel_dump_traceback_later()
