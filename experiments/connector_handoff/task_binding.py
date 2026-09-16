"""Task vocabulary bindings; the frozen AP implementation executes unchanged."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def questions_for(fact):
    f=fact[1:] if fact[0]=='not' else fact
    if f[0]=='inview':
        name=f[2].replace('_',' ')
        return (f'Is the {name} visible in this image?',f'Can you see the {name} in this view?',
                f'Is the {name} present and visible in this image?',f'Does this image contain the {name}?',
                f'Is the {name} observable from this viewpoint?')
    if f[0] in ('side_clear_left','side_clear_right'):
        side=f[0].split('_')[-1]
        return (f'Is there sufficient clearance on the {side} side of the socket?',
                f'Is the {side} side of the socket free of obstructing fixture geometry?',
                f'Is there open space beside the {side} side of the socket?',
                f'Is the approach corridor beside the {side} of the socket unobstructed?',
                f'Is the space adjacent to the {side} side of the socket clear?')
    if f[0]=='inserted':
        return ('Is the connector inserted into the socket?', 'Is the connector seated in the socket?',
                'Has the connector entered the socket to its seated position?',
                'Is the connector engaged inside the socket?', 'Is the connector fully seated in the socket?')
    raise ValueError(f'Unmapped connector visual predicate: {f[0]}')


def verifier_class():
    # A private module instance binds task vocabulary without mutating the shared
    # baseline module or any source file. All methods/control flow are identical.
    spec=importlib.util.spec_from_file_location('connector_bound_paper_adapter',ROOT/'vlm-tamp/paper_sim_adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.questions_for=questions_for
    return module.PaperSimVerifier
