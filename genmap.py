#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import random


map_ = [['a'] + ['-' for i in range(512)] + ['a'] for j in range(512)]
map_.insert(0, ['a' for i in range(514)])
map_.append(['a' for i in range(514)])


def fake_data():
    for i in range(50):
        yield random.randint(1, 10)


def print_map(map_):
    for row in map_:
        for c in row:
            print(c, end='')
        print()


def add_to_map(duration):
    pass


for duration in fake_data():
    add_to_map(duration)


print_map(map_)
