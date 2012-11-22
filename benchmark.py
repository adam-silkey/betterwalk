"""Simple benchmark to compare the speed of BetterWalk with os.walk()."""

import optparse
import os
import stat
import sys
import timeit

import betterwalk

DEPTH = 4
NUM_DIRS = 5
NUM_FILES = 50

def create_tree(path, depth=DEPTH):
    """Create a directory tree at path with given depth, and NUM_DIRS and
    NUM_FILES at each level.
    """
    os.mkdir(path)
    for i in range(NUM_FILES):
        filename = os.path.join(path, 'file{0:03}.txt'.format(i))
        with open(filename, 'wb') as f:
            line = 'The quick brown fox jumps over the lazy dog.\n'
            if i == 0:
                # So we have at least one big file per directory
                f.write(line * 20000)
            else:
                f.write(line * i * 10)
    if depth <= 1:
        return
    for i in range(NUM_DIRS):
        dirname = os.path.join(path, 'dir{0:03}'.format(i))
        create_tree(dirname, depth - 1)

def get_tree_size(path):
    """Return total size of all files in directory tree at path."""
    size = 0
    try:
        for name, st in betterwalk.iterdir_stat(path, fields=['st_mode_type', 'st_size']):
            if stat.S_ISDIR(st.st_mode):
                size += get_tree_size(os.path.join(path, name))
            else:
                size += st.st_size
    except OSError:
        pass
    return size

def benchmark(path, get_size=False):
    sizes = {}

    if get_size:
        def do_os_walk():
            size = 0
            for root, dirs, files in os.walk(path):
                for filename in files:
                    fullname = os.path.join(root, filename)
                    size += os.path.getsize(fullname)
            sizes['os_walk'] = size

        def do_betterwalk():
            sizes['betterwalk'] = get_tree_size(path)

    else:
        def do_os_walk():
            for root, dirs, files in os.walk(path):
                pass

        def do_betterwalk():
            for root, dirs, files in betterwalk.walk(path):
                pass

    # Run this once first to cache things, so we're not benchmarking I/O
    print("Priming the system's cache...")
    do_betterwalk()

    # Use the best of 3 time for each of them to eliminate high outliers
    os_walk_time = 1000000
    betterwalk_time = 1000000
    N = 3
    for i in range(N):
        print('Benchmarking walks on {0}, repeat {1}/{2}...'.format(
            path, i + 1, N))
        os_walk_time = min(os_walk_time, timeit.timeit(do_os_walk, number=1))
        betterwalk_time = min(betterwalk_time, timeit.timeit(do_betterwalk, number=1))

    if get_size:
        if sizes['os_walk'] == sizes['betterwalk']:
            equality = 'equal'
        else:
            equality = 'NOT EQUAL!'
        print('os.walk size {0}, BetterWalk size {1} -- {2}'.format(
            sizes['os_walk'], sizes['betterwalk'], equality))

    print('os.walk took {0:.3f}s, BetterWalk took {1:.3f}s -- {2:.3f}x as fast'.format(
          os_walk_time, betterwalk_time, os_walk_time / betterwalk_time))

def main():
    """Usage: benchmark.py [-h] [tree_dir]

Create 230MB directory tree named "benchtree" (relative to this script) and
benchmark os.walk() versus betterwalk.walk(). If tree_dir is specified,
benchmark using it instead of creating a tree.
"""
    parser = optparse.OptionParser(usage=main.__doc__.rstrip())
    parser.add_option('-s', '--size', action='store_true',
                      help='get size of directory tree while walking')
    options, args = parser.parse_args()

    if args:
        tree_dir = args[0]
    else:
        tree_dir = os.path.join(os.path.dirname(__file__), 'benchtree')
        if not os.path.exists(tree_dir):
            print 'Creating tree at {0}: depth={1}, num_dirs={2}, num_files={3}'.format(
                tree_dir, DEPTH, NUM_DIRS, NUM_FILES)
            create_tree(tree_dir)

    benchmark(tree_dir, get_size=options.size)

if __name__ == '__main__':
    main()
