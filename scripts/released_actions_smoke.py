"""Isolated execution of released task primitives; no VLM or verification trial."""
import ast
import hashlib
import os
from pathlib import Path
import sys


def run(root, out, env, event):
    import numpy as np

    source_path = root / 'vlm-tamp/eval.py'
    source = source_path.read_text()
    nodes = []
    for node in ast.parse(source).body:
        targets = [x.id for x in getattr(node, 'targets', []) if isinstance(x, ast.Name)]
        if 'config_filename' in targets:
            break
        if 'vlm_agent' in targets:
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.Assign, ast.If)):
            nodes.append(node)
    sys.path.insert(0, str(root / 'vlm-tamp'))
    scope = dict(__name__='released_primitive_diagnostic', __file__=str(source_path))
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source_path), 'exec'), scope)
    work = out / 'released_actions'
    work.mkdir()
    for name in ('downward', 'VAL'):
        (work / name).symlink_to(root / 'vlm-tamp' / name)
    third = work / 'third_person'
    first = work / 'first_person'
    third.mkdir()
    first.mkdir()
    robot = env.robots[0]
    scope.update(env=env, robot=robot, scene=env.scene,
                 robot_init_z=robot.get_position()[2],
                 ap=scope['StarterSemanticActionPrimitives'](env),
                 obj_held=None, filled=None, inside_relationships=[], onfloor_relationships=[],
                 sim_counter=0, debug_path=str(third), run_dir=str(work),
                 trial_counter=0, action_counter=0, record=event)
    # Released bringing_water task override near the start of the episode.
    scope['PICK_OBJ_HEIGHT'] = 2.0
    scope['random'].seed(0)
    np.random.seed(0)
    scope['watch_robot']()
    domain = root / 'vlm-tamp/domains/bringing_water/domain.pddl'
    problem = root / 'vlm-tamp/domains/bringing_water/problem.pddl'
    planner = scope['pddlsim'](str(domain))
    previous = Path.cwd()
    try:
        os.chdir(work)
        plan = planner.plan(str(problem))
        assert plan and planner.get_intermediate_states(str(problem), 'pddl_output.txt')
        event('scripted_plan_started', kind='primitive_smoke_without_verification', seed=0,
              source_sha256=hashlib.sha256(source.encode()).hexdigest(), plan=plan,
              failure_probabilities_preserved=True)
        for index, action in enumerate(plan):
            params = scope['format_action_params'](action)
            method = {'find': 'goto', 'grasp': 'grasp', 'place_on_floor': 'place_on_floor'}[action[0]]
            event('scripted_action_started', index=index, action=action)
            result = scope[method](params[1], oracle=False)
            event('scripted_action_completed', index=index, action=action,
                  returned=result,
                  simulator_state=scope['simulator_state'](env, scope['obj_held'], scope['onfloor_relationships']),
                  object_positions={name: value.get_position().tolist()
                    for name, value in env.task.object_scope.items() if value.exists and hasattr(value, 'get_position')},
                  held_object=None if scope['obj_held'] is None else scope['obj_held'].name,
                  onfloor_relationships=list(scope['onfloor_relationships']))
            if method == 'goto' and result is False:
                raise RuntimeError('Released navigation found no valid pose; stopping primitive check')
        bottles = ['water_bottle.n.01_1', 'water_bottle.n.01_2']
        released_goal = all(0 < env.task.object_scope[name].get_position()[2] < 0.1
                            and name in scope['onfloor_relationships'] for name in bottles)
        event('scripted_plan_completed', executed_actions=len(plan), released_goal=bool(released_goal),
              scope='no VLM, no predicate verification or replanning; not a VAP-TAMP trial')
    finally:
        os.chdir(previous)
        from episode_videos import encode_videos
        for video in encode_videos(work):
            event('scripted_video_saved', **video)
