#!/usr/bin/env python3
## USAGE: ./recursive_gen.sh DIRECTORY
## will recursively put all files from DIRECTORY into ../data/YYYY-MM-DD.HH-MM-SS/*, matching the directory structure

import argparse
import os
import subprocess
import sys
import multiprocessing
import time

try:
    from tqdm import tqdm
except:
    tqdm = lambda x: x

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

    for (dirpath, dirnames, filenames) in tqdm(list(os.walk(directory))):
        if '.git' in dirpath:
            continue
        for fname in filenames:
            if not fname.endswith('.ts'):
                continue

            fname_with_json = fname[:-2] + 'json'
            src = os.path.join(dirpath, fname)
            dst_dir = os.path.join(rootdir, os.path.relpath(dirpath, directory))
            dst = os.path.join(dst_dir, fname_with_json)
            os.makedirs(os.path.join(_DIRNAME, os.pardir, 'data', dst_dir), exist_ok=True)

            queue.put((src, dst))

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
