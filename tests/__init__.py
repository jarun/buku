import os
from contextlib import contextmanager


@contextmanager
def environ(**env):
    originals = {k: os.environ.get(k) for k in env}
    for k, val in env.items():
        if val is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = val
    try:
        yield
    finally:
        for k, val in originals.items():
            if val is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = val
