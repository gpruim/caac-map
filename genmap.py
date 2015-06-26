#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import math
import random


class ResourceMap(list):

    def __init__(self, canvas_size, sum_of_durations):
        self.H = self.W = canvas_size
        self.area = self.H * self.W
        self.sum_of_durations = sum_of_durations

        # Build the base map. It's surrounded by alleys, so it's effectively
        # 1-indexed.
        padded = lambda row: ['a'] + row + ['a']
        top_and_bottom = lambda: padded(['a' for i in range(self.W)])
        self.extend([padded(['-' for i in range(self.W)]) for j in range(self.H)])
        self.insert(0, top_and_bottom())
        self.append(top_and_bottom())

    def __str__(self):
        return '\n'.join([''.join([c for c in row]) for row in self])

    def add_resource(self, duration):

        # Find first empty cell.
        x = y = 0
        while 1:
            if self[x][y] == '-':
                break
            x += 1
            if x > self.W:
                x = 0
                y += 1

        # Determine target area.
        target_area = int(self.area * (duration / self.sum_of_durations))
        assert target_area >= 16

        # Get a list of candidate shapes.
        candidates = self._get_candidate_shapes(target_area)

        # Weight the list of candidate shapes.
        pass

        # Pick a shape and draw it!
        shape = random.choice(candidates)
        self._draw_shape_at(shape, x, y)


    def _draw_shape_at(self, shape, x, y):
        w, h = shape
        for i in range(x, x+w+1):
            for j in range(y, y+h+1):
                self[i][j] = '#'


    def _get_candidate_shapes(self, target_area):
        lo = 4
        hi = None

        while 1:
            hi = int(math.floor(target_area / lo))
            if lo / hi >= 0.2:
                break
            else:
                lo += 1

        candidates = []
        for w in range(lo, hi+1):
            for h in range(lo, hi+1):
                candidates.append((w, h))

        return candidates


def fake_data():
    for i in range(50):
        yield 32 * random.randint(1, 10)


if __name__ == '__main__':
    durations = list(fake_data())
    resource_map = ResourceMap(canvas_size=512, sum_of_durations=sum(durations))
    for duration in durations:
        resource_map.add_resource(duration)
        break
    print(resource_map)
