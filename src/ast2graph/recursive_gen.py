#!/usr/bin/env python3
## USAGE: ./recursive_gen.sh DIRECTORY
## will recursively put all files from DIRECTORY into ../data/YYYY-MM-DD.HH-MM-SS/*, matching the directory structure

import argparse
import multiprocessing
import os
import subprocess
import sys
import time
from tqdm import tqdm

_DIRNAME = os.path.abspath(os.path.dirname(__file__))

def run_multiproc(q):
    while True:
        n = q.get()
        if n == None:
            return

        (src, dst) = n
        subprocess.run([
            '/usr/bin/env',
            'node',
            os.path.join(_DIRNAME, 'build', 'main.js'),
            src,
            dst,
        ], cwd=_DIRNAME, stdout=subprocess.DEVNULL)


def gen(directory, n_procs=8):
    rootdir = time.strftime('%Y-%m-%d.%H-%M-%S')

    queue = multiprocessing.Queue(n_procs + 2)
    procs = [multiprocessing.Process(target=run_multiproc, args=(queue,), daemon=True) for _ in range(n_procs)]
    for proc in procs:
        proc.start()

    if not os.path.isdir(directory):
        raise ValueError('{} is not a known directory!'.format(directory))

    for dname in tqdm(os.listdir(directory)):
        src_dir = os.path.join(directory, dname)
        dst_dir = os.path.join(_DIRNAME, os.pardir, 'data', rootdir, dname)
        queue.put((src_dir, dst_dir))

    for proc in procs:
        queue.put(None)
        proc.join()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', help='The directory to recursively traverse')
    args = parser.parse_args()

    sys.exit(gen(args.directory))

if __name__ == '__main__':
    main()
