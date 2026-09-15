"""Read-only diagnostics for the intermittent native USD traversal exception."""
import dis
import functools
import hashlib
import inspect
import marshal
from pathlib import Path
import sys


def install(event):
    import omni.isaac.core.utils.prims as prims
    original = prims.get_all_matching_child_prims
    code = original.__code__
    event('usd_traversal_identity', filename=code.co_filename,
          source_sha256=hashlib.sha256(Path(code.co_filename).read_bytes()).hexdigest(),
          code_sha256=hashlib.sha256(marshal.dumps(code)).hexdigest(),
          source=inspect.getsource(original), trace_hook=repr(sys.gettrace()),
          profile_hook=repr(sys.getprofile()))

    @functools.wraps(original)
    def traced(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except BaseException as error:
            tb = error.__traceback__
            frames = []
            while tb:
                frame = tb.tb_frame
                if frame.f_code is code:
                    frames.append(dict(line=tb.tb_lineno, instruction=tb.tb_lasti,
                        local_types={k: type(v).__name__ for k, v in frame.f_locals.items()},
                        scalar_locals={k: v for k, v in frame.f_locals.items()
                                       if type(v) in (str, int, float, bool, type(None))},
                        bytecode=dis.Bytecode(code).dis()))
                tb = tb.tb_next
            event('usd_traversal_exception', frames=frames, exception_type=type(error).__name__)
            raise
    prims.get_all_matching_child_prims = traced
