"""Process-local settings for the audited native simulator on this machine."""
import os


def apply_cpu_affinity():
    value = os.getenv('VAPTAMP_CPU_AFFINITY')
    if not value:
        return sorted(os.sched_getaffinity(0))
    cpus = set()
    for part in value.split(','):
        limits = part.split('-')
        if len(limits) == 1:
            cpus.add(int(part))
        elif len(limits) == 2:
            cpus.update(range(int(limits[0]), int(limits[1]) + 1))
        else:
            raise ValueError('Invalid VAPTAMP_CPU_AFFINITY')
    if not cpus or not cpus.issubset(os.sched_getaffinity(0)):
        raise ValueError('Requested CPU affinity is not available to this process')
    os.sched_setaffinity(0, cpus)
    return sorted(os.sched_getaffinity(0))
