#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import math
import random


A = '\u2591'    # Alley
B = '\u2593'    # Block/Building
C = ' '         # Canvas


class MagnitudeMap(list):

    def __init__(self, canvas_size, sum_of_magnitudes):
        self.W, self.H = canvas_size
        self.area = self.W * self.H
        self.sum_of_magnitudes = sum_of_magnitudes

        # Build the base map. It's surrounded by alleys, which are four units wide.
        padded = lambda col: [A,A,A,A] + col + [A,A,A,A]
        col = lambda char: self.append(padded([char for y in range(self.H)]))
        for x in range(4):      col(A)
        for x in range(self.W): col(C)
        for x in range(4):      col(A)

    def __unicode__(self):
        out = []
        alleys = 8
        for y in range(self.H + alleys):
            for x in range(self.W + alleys):
                out.append(self[x][y])
            out.append('\n')
        return ''.join(out[:-1])

    def __str__(self):
        return unicode(self).encode('UTF-8')

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
        candidates = self._get_candidate_shapes(x, y, target_area)
        if not candidates:
            return

        # Weight the list of candidate shapes.
        pass

        # Pick a shape and draw it!
        shape = random.choice(candidates)
        self._draw_shape_at(shape, x, y)


    def _draw_shape_at(self, shape, x, y):
        w, h = shape
        for x_ in range(x, x+w+1):
            for y_ in range(y, y+h+1):
                self[x_][y_] = B

        self._draw_alleys_around_shape(w, h, x, y)


    def _draw_alleys_around_shape(self, w, h, x, y):
        left, right = x, x+w+1
        top, bottom = y, y+h+1

        def draw_alley(x,y):
            assert self[x][y] in (C, A)
            self[x][y] = A

        for x in range(right, right+4):
            for y in range(top-4, bottom+4):
                draw_alley(x,y)

        for x in range(left-4, left):
            for y in range(top-4, bottom+4):
                draw_alley(x,y)

        for x in range(left, right):
            for y in range(top-4, top):
                draw_alley(x,y)

        for x in range(left, right):
            for y in range(bottom, bottom+4):
                draw_alley(x,y)


    def _get_candidate_shapes(self, x, y, target_area):
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

                if self._not_enough_room(x, y, w, h):
                    continue

                candidates.append((w, h))

        return candidates


    def _not_enough_room(self, x, y, w, h):
        try:
            if self[x+w][y+h] != C:
                return True
        except IndexError:
            return True
        return False


def fake_data():
    for i in range(50):
        yield 32 * random.randint(1, 10)


if __name__ == '__main__':
    magnitudes = list(fake_data())
    magnitude_map = MagnitudeMap(canvas_size=(512, 512), sum_of_magnitudes=sum(magnitudes))
    for magnitude in magnitudes:
        magnitude_map.add(magnitude)
    print(magnitude_map)
