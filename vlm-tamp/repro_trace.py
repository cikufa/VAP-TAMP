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
