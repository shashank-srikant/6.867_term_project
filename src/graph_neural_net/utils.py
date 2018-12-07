import os
import random
import time
from tqdm import tqdm
from typing import Any, Dict, Iterable, List, Optional, TypeVar
import pickle as pkl

#DIRNAME = os.path.abspath(os.path.dirname(__file__))
DIRNAME = '../../data/'

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

def flatten(lst: Iterable[Iterable[V]]) -> List[V]:
    return [i for l in lst for i in l]

class defaultdict_nowrite(dict):
    def __init__(self, default_factory, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.default_factory = default_factory

    def __missing__(self, key):
        return self.default_factory()

def write(obj: Any, fname:Optional[str]=None, fappend:bool=False, nolog:bool=False) -> None:
    to_write = str(obj)
    if fname:
        full_fname = os.path.join(DIRNAME, fname)
        dirname = os.path.dirname(full_fname)
        os.makedirs(dirname, exist_ok=True)
        if fappend:
            flags = 'a'
        else:
            flags = 'w'
        with open(full_fname, flags) as f:
            print(to_write, file=f)

    if nolog:
        tqdm.write(to_write)
    else:
        log(obj)

def log(obj: Any) -> None:
    return write(obj, os.path.join('logs', get_time_str()), True, True)

def save_data(directory: str, **kwargs):
    os.makedirs(os.path.join(DIRNAME, directory), exist_ok=True)
    for k, v in kwargs.items():
        with open(os.path.join(DIRNAME, directory, k), 'wb') as fp:
            pkl.dump(v, fp)
            fp.close()

def load_train_test_data(directory: str):
    kwargs = {}
    for f in os.listdir(os.path.join(DIRNAME, directory)):
        with open(os.path.join(DIRNAME, directory, f), 'rb') as fp:
            kwargs[f] = pkl.load(fp)

    return [kwargs['train_names'],
            kwargs['train_graph_jsons'],
            kwargs['test_names'],
            kwargs['test_graph_jsons'],
            kwargs['index_maps']]
