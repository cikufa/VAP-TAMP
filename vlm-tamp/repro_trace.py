"""Opt-in append-only provenance; no planner or simulator decisions."""
import itertools
import json
import os
from pathlib import Path
import time

_sequence = itertools.count()


def simulator_state(env, held=None, onfloor=()):
    """Diagnostic ground truth for logs only; never supplied to a VLM/planner."""
    objects = {}
    for name, entity in env.task.object_scope.items():
        if entity.exists and hasattr(entity, 'get_position_orientation'):
            position, orientation = entity.get_position_orientation()
            objects[name] = dict(position=position.tolist(), orientation=orientation.tolist())
    return dict(objects=objects, robot_joint_positions=env.robots[0].get_joint_positions().tolist(),
                held=None if held is None else held.name, onfloor_relationships=list(onfloor))


def final_goal_diagnostics(env, task_name, held=None, onfloor=()):
    """Read-only scoring evidence; never changes released scoring or planning.

    BEHAVIOR's cabinet goal and the released bringing_water floor goal differ.
    Report both explicitly, including physical OnTop and the released z proxy.
    """
    from bddl.activity import evaluate_goal_conditions
    from omnigibson.object_states import OnTop

    achieved, status = evaluate_goal_conditions(env.task.activity_goal_conditions)
    result = dict(simulator_state=simulator_state(env, held, onfloor),
                  native_bddl_success=bool(achieved), native_bddl_status=status,
                  native_bddl_goal=env.task.activity_conditions.parsed_goal_conditions)
    if task_name == 'bringing_water':
        floor = env.task.object_scope['floor.n.01_1'].wrapped_obj
        bottles = {}
        for name in ('water_bottle.n.01_1', 'water_bottle.n.01_2'):
            obj = env.task.object_scope[name].wrapped_obj
            position = obj.get_position()
            lower, upper = obj.aabb
            bottles[name] = dict(
                model=obj.model, position=position.tolist(),
                aabb_lower=lower.tolist(), aabb_upper=upper.tolist(),
                room_instance=env.scene.seg_map.get_room_instance_by_point(position[:2]),
                on_target_floor=bool(obj.states[OnTop].get_value(floor)),
                released_height_proxy=bool(0 < position[2] < 0.1),
                released_onfloor_tracker=name in onfloor,
            )
        result.update(bottles=bottles, target_floor_rooms=list(floor.in_rooms),
                      physical_released_pddl_goal=all(
                          bottle['on_target_floor'] for bottle in bottles.values()))
    return result


def record(event, **fields):
    directory = os.getenv('VAPTAMP_TRACE_DIR')
    if not directory:
        return
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=True)
    payload = dict(sequence=next(_sequence), monotonic_ns=time.monotonic_ns(),
                   utc_unix_ns=time.time_ns(), event=event, **fields)
    with (destination / 'events.jsonl').open('a') as output:
        output.write(json.dumps(payload) + '\n')
