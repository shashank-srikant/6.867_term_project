import os
import random
import time
from typing import Dict, List, TypeVar

DIRNAME = os.path.abspath(os.path.dirname(__file__))

K = TypeVar('K')
V = TypeVar('V')

def invert_bijective_dict(d: Dict[K, V]) -> Dict[V, K]:
    return {v:k for (k, v) in d.items()}

_time_str = None
def get_time_str() -> str:
    global _time_str
    if _time_str is None:
        _time_str = time.strftime('%Y-%m-%d.%H-%M-%S')
    return _time_str

def set_random_seed(seed: int) -> None:
    if seed < 0:
        random.seed(None)
    else:
        random.seed(seed)

def flatten(lst: List[List[V]]) -> List[V]:
    return [i for l in lst for i in l]

class defaultdict_nowrite(dict):
    def __init__(self, default_factory, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.default_factory = default_factory

    def __missing__(self, key):
        return self.default_factory()
