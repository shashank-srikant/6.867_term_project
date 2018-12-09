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
import concurrent.futures

_DIRNAME = os.path.abspath(os.path.dirname(__file__))

def run_multiproc(n):
    (src, dst) = n
    subprocess.run([
        '/usr/bin/env',
        'node',
        os.path.join(_DIRNAME, 'build', 'main_baseline.js'),
        src,
        dst,
    ], cwd=_DIRNAME, timeout=5, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def gen(directory, n_procs=2):
    rootdir = time.strftime('%Y-%m-%d.%H-%M-%S')
    arg_list = []
    if not os.path.isdir(directory):
        raise ValueError('{} is not a known directory!'.format(directory))

    for dname in tqdm(os.listdir(directory)):
        src_dir = os.path.join(directory, dname)
        dst_dir = os.path.join(_DIRNAME, os.pardir, os.pardir, 'data/repo/6867/', rootdir, dname)
        arg_list.append((src_dir, dst_dir))

    print(arg_list)
    with concurrent.futures.ProcessPoolExecutor() as pool:
        try:
            out = pool.map(run_multiproc, arg_list)
        except Exception as e:
            print('oops. timed out')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', help='The directory to recursively traverse')
    args = parser.parse_args()

    sys.exit(gen(args.directory))

if __name__ == '__main__':
    main()
