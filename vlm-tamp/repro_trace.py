"""Opt-in append-only provenance; no planner or simulator decisions."""
import itertools
import json
import os
from pathlib import Path
import time

_sequence = itertools.count()


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
