#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import math
import random


A = '\u2591'    # Alley
B = '\u2593'    # Block/Building
C = ' '         # Canvas


class MagnitudeMap(list):

    def __init__(self, canvas_size, sum_of_magnitudes):
        self.H = self.W = canvas_size
        self.area = self.H * self.W
        self.sum_of_magnitudes = sum_of_magnitudes

        # Build the base map. It's surrounded by alleys, which are four units wide.
        padded = lambda row: [A,A,A,A] + row + [A,A,A,A]
        top_or_bottom = lambda: padded([A for i in range(self.W)])
        self.extend([padded([C for i in range(self.W)]) for j in range(self.H)])
        for i in range(4):
            self.insert(0, top_or_bottom())
            self.append(top_or_bottom())

    def __str__(self):
        return '\n'.join([''.join([c for c in row]) for row in self]).encode('UTF-8')

    def __unicode__(self):
        return str(self).decode('UTF-8')

    def add(self, magnitude):

        # Find first empty cell.
        x = y = 0
        while 1:
            if self[x][y] == C:
                break
            x += 1
            if x > self.W:
                x = 0
                y += 1

        # Determine target area.
        target_area = int(self.area * (magnitude / self.sum_of_magnitudes))
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
                self[i][j] = B

        self._draw_alleys_around_shape(w, h, x, y)


    def _draw_alleys_around_shape(self, w, h, x, y):
        left, right = x, x+w+1
        top, bottom = y, y+h+1

        def draw_alley(i,j):
            assert self[i][j] in (C, A)
            self[i][j] = A

        for i in range(right, right+4):
            for j in range(top-4, bottom+4):
                draw_alley(i,j)

        for i in range(left-4, left):
            for j in range(top-4, bottom+4):
                draw_alley(i,j)

        for i in range(left, right):
            for j in range(top-4, top):
                draw_alley(i,j)

        for i in range(left, right):
            for j in range(bottom, bottom+4):
                draw_alley(i,j)


    def _get_candidate_shapes(self, target_area):
        lo = 4
        hi = None

        while 1:
            hi = int(math.floor(target_area / lo))
            if lo / hi >= 0.2:
                break  # maintain a certain minimum aspect ratio
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
    magnitudes = list(fake_data())
    magnitude_map = MagnitudeMap(canvas_size=512, sum_of_magnitudes=sum(magnitudes))
    for magnitude in magnitudes:
        magnitude_map.add(magnitude)
        break
    print(magnitude_map)
