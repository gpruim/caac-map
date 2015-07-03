#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import math
import random


class NoPossibleShapes(Exception): pass
class TargetAreaTooSmall(Exception): pass
class UnevenAlleys(Exception): pass


class MagnitudeMap(list):

    A = '-' # Alley
    B = '#' # Block/Building
    C = ' ' # Canvas

    def __init__(self, canvas_size, sum_of_magnitudes=0, chars='-# ', alley_width=2, block_min=4,
            area_threshold=1):
        self.W, self.H = canvas_size
        self.area = self.W * self.H
        self.sum_of_magnitudes = sum_of_magnitudes
        self.A, self.B, self.C = chars
        if alley_width % 2 == 1:
            raise UnevenAlleys()
        self.alley_width = alley_width
        self.half_alley = alley_width // 2
        self.block_min = block_min
        self.area_threshold = area_threshold

        # Build the base map. It's surrounded by alleys.

        half_alley = lambda P=self.A: [P] * self.half_alley
        padded = lambda col, P: half_alley() + half_alley(P) + col + half_alley(P) + half_alley()
        col = lambda char, P: self.append(padded([char for y in range(self.H)], P))
        for x in range(self.half_alley):    col(self.A, self.A)
        for x in range(self.half_alley):    col(self.C, self.C)
        for x in range(self.W):             col(self.C, self.C)
        for x in range(self.half_alley):    col(self.C, self.C)
        for x in range(self.half_alley):    col(self.A, self.A)

    def __unicode__(self):
        out = []
        alleys = self.alley_width * 2
        for y in range(self.H + alleys):
            for x in range(self.W + alleys):
                out.append(self[x][y])
            out.append('\n')
        return ''.join(out[:-1])

    def __str__(self):
        return unicode(self).encode('UTF-8')


    def find_first_empty_cell(self):
        x = y = 0
        while 1:
            if self[x][y] == self.C:
                break
            x += 1
            if x > self.W:
                x = 0
                y += 1
        return x, y


    def determine_target_area(self, magnitude):
        target_area = int(self.area * (magnitude / self.sum_of_magnitudes))
        min_area = self.block_min ** 2
        if target_area < min_area:
            raise TargetAreaTooSmall()
        return target_area


    def add(self, magnitude, shape_choice=None):

        # Find first empty cell.
        x, y = self.find_first_empty_cell()

        # Determine target area.
        target_area = self.determine_target_area(magnitude)

        # Try to find a nice fit. If we can't make it work, introduce some jitter.
        shapes = self.get_snapped_shapes(x, y, target_area)

        # Weight the list of candidate shapes.
        pass

        if not shapes:
            raise NoPossibleShapes()

        # Pick a shape and draw it!
        if shape_choice is not None:
            shape = shapes[shape_choice]
        else:
            shape = random.choice(shapes)
        self.draw_shape_at(shape, x, y)


    def draw_shape_at(self, shape, x, y):
        w, h = shape
        for x_ in range(x, x+w):
            for y_ in range(y, y+h):
                try:
                    self[x_][y_] = self.B
                except IndexError:
                    print(shape, x, y)
                    print(x_, y_, len(self), len(self[y_]))
                    print(self)
                    raise

        self.draw_alleys_around_shape(shape, x, y)


    def draw_alleys_around_shape(self, shape, x, y):
        w, h = shape
        left, right = x, x+w
        top, bottom = y, y+h

        def draw_alley(x,y):
            assert self[x][y] in (self.C, self.A)
            self[x][y] = self.A

        for x in range(right, right + self.alley_width):
            for y in range(top - self.alley_width, bottom + self.alley_width):
                draw_alley(x,y)

        for x in range(left - self.alley_width, left):
            for y in range(top - self.alley_width, bottom + self.alley_width):
                draw_alley(x,y)

        for x in range(left, right):
            for y in range(top - self.alley_width, top):
                draw_alley(x,y)

        for x in range(left, right):
            for y in range(bottom, bottom + self.alley_width):
                draw_alley(x,y)


    def get_snapped_shapes(self, x, y, target_area):
        """Return a list of shapes we can reasonably snap to.

        We can snap in one or two directions. If we can snap in two directions,
        then the return list will only have one item: the two-snapped shape. If
        we can't snap in two directions but we can snap in one or the other
        direction, then we return a list of all the possible shapes snapped in
        either direction.

        """

        right_bounds = self.get_right_bounds(x, y)
        bottom_bounds = self.get_bottom_bounds(x, y)

        two_snappers = []
        for right_bound in right_bounds:
            for bottom_bound in bottom_bounds:
                w = right_bound - x
                h = bottom_bound - y
                if w < self.block_min or h < self.block_min:
                    continue
                candidate_area = w * h
                delta = abs(target_area - candidate_area)
                threshold = target_area - (target_area * self.area_threshold)
                if delta <= threshold:
                    shape = (w, h)
                    two_snappers.append(shape)

        if two_snappers:
            return two_snappers

        one_snappers = []
        for right_bound in right_bounds:
            w = right_bound - x
            h = target_area // w
            if h >= self.block_min:
                one_snappers.append((w,h))
        for bottom_bound in bottom_bounds:
            h = bottom_bound - y
            w = target_area // h
            if w >= self.block_min:
                one_snappers.append((w,h))
        return one_snappers

    def get_right_bounds(self, x, y):
        right_bounds = []
        while x < self.alley_width + self.W:
            x += 1
            if self[x][y] == self.A:
                right_bounds.append(x)
        return right_bounds


    def get_bottom_bounds(self, x, y):
        bottom_bounds = []
        while y < self.H + self.alley_width:
            y += 1
            if self[x][y] == self.A:
                bottom_bounds.append(y)
        return bottom_bounds


    def _get_unsnapped_shapes(self, x, y, target_area):
        lo = self.alley_width
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
            if self[x+w][y+h] != self.C:
                return True
        except IndexError:
            return True
        return False


def fake_data():
    for i in range(50):
        yield 32 * random.randint(1, 10)


if __name__ == '__main__':
    magnitudes = list(fake_data())
    magnitude_map = MagnitudeMap( canvas_size=(512, 512)
                                , sum_of_magnitudes=sum(magnitudes)
                                , chars='\u2591\u2593 '
                                 )
    for magnitude in magnitudes:
        magnitude_map.add(magnitude)
    print(magnitude_map)
