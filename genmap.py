#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

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
        if alley_width % 2 == 1: raise UnevenAlleys()
        self.alley_width = alley_width
        self.remaining_area = (self.W - alley_width) * (self.H - alley_width)
        self.remaining_magnitudes = sum_of_magnitudes
        self.A, self.B, self.C = chars
        self.half_alley = alley_width // 2
        self.shape_min = block_min + alley_width
        self.area_threshold = area_threshold

        # Build the base map. It's surrounded by alleys.

        innerW = self.W - (self.alley_width * 2)
        innerH = self.H - (self.alley_width * 2)
        half_alley = lambda P=self.A: [P] * self.half_alley
        padded = lambda col, P: half_alley() + half_alley(P) + col + half_alley(P) + half_alley()
        col = lambda char, P: self.append(padded([char for y in range(innerH)], P))
        for x in range(self.half_alley):    col(self.A, self.A)
        for x in range(self.half_alley):    col(self.C, self.C)
        for x in range(innerW):             col(self.C, self.C)
        for x in range(self.half_alley):    col(self.C, self.C)
        for x in range(self.half_alley):    col(self.A, self.A)

    def __unicode__(self):
        out = []
        for y in range(self.H):
            for x in range(self.W):
                out.append(self[x][y])
            out.append('\n')
        return ''.join(out[:-1])

    def __str__(self):
        return unicode(self).encode('UTF-8')


    def find_starting_corner(self):
        x = y = 0
        while 1:
            if self[x][y] == self.C:
                break
            x += 1
            if x == self.W:
                x = 0
                y += 1
        return x, y


    def determine_target_area(self, magnitude):
        target_area = int(self.remaining_area * (magnitude / self.remaining_magnitudes))
        min_area = self.shape_min ** 2
        if target_area < min_area:
            raise TargetAreaTooSmall()
        return target_area


    def add(self, magnitude, shape_choice=None):

        # Find first empty cell.
        x, y = self.find_starting_corner()

        # Determine target area.
        target_area = self.determine_target_area(magnitude)

        # Try to find a nice fit. If we can't make it work, introduce some jitter.
        shapes = self.get_snapped_shapes(x, y, target_area)
        if not shapes:
            shapes = self.get_unsnapped_shapes(x, y, target_area)

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

        # Decrement remaining_magnitudes.
        self.remaining_magnitudes -= magnitude


    def place_tile(self, tile, x, y):
        assert self[x][y] == self.C
        self[x][y] = tile
        self.remaining_area -= 1


    def draw_shape_at(self, shape, x, y):
        w, h = [dimension - self.alley_width for dimension in shape]
        x = x + self.half_alley
        y = y + self.half_alley
        for x_ in range(x, x+w):
            for y_ in range(y, y+h):
                try:
                    self.place_tile(self.B, x_, y_)
                except IndexError:
                    print(shape, x, y)
                    print(x_, y_, len(self), len(self[y_]))
                    print(self)
                    raise

        self.draw_half_alleys_around_shape((w,h), x, y)


    def draw_half_alleys_around_shape(self, shape, x, y):
        w, h = shape
        left, right = x, x+w
        top, bottom = y, y+h

        def place_alley_tile(x, y):
            if self[x][y] != self.A:
                self.place_tile(self.A, x, y)

        for x in range(right, right + self.half_alley):
            for y in range(top - self.half_alley, bottom + self.half_alley):
                place_alley_tile(x, y)

        for x in range(left - self.half_alley, left):
            for y in range(top - self.half_alley, bottom + self.half_alley):
                place_alley_tile(x, y)

        for x in range(left, right):
            for y in range(top - self.half_alley, top):
                place_alley_tile(x, y)

        for x in range(left, right):
            for y in range(bottom, bottom + self.half_alley):
                place_alley_tile(x, y)


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


        # Two-Snappers
        # ============

        two_snappers = []

        big_enough = lambda w, h: w >= self.shape_min and h >= self.shape_min

        for right_bound in right_bounds:
            for bottom_bound in bottom_bounds:
                w = right_bound - x
                h = bottom_bound - y
                if not big_enough(w, h):
                    continue
                candidate_area = w * h
                delta = abs(target_area - candidate_area)
                threshold = target_area - (target_area * self.area_threshold)
                if delta <= threshold:
                    shape = (w, h)
                    two_snappers.append(shape)

        if two_snappers:
            return two_snappers


        # One-Snappers
        # ============

        one_snappers = []

        def enough_canvas(x, y):
            try:
                return self[x][y] == self.C
            except IndexError:
                return False

        for right_bound in right_bounds:
            w = right_bound - x
            h = target_area // w
            while not enough_canvas(x, y + h-1 + self.shape_min):
                h -= 1
            if big_enough(w, h):
                one_snappers.append((w, h))

        for bottom_bound in bottom_bounds:
            h = bottom_bound - y
            w = target_area // h
            while not enough_canvas(x + w-1 + self.shape_min, y):
                w -= 1
            if big_enough(w, h):
                one_snappers.append((w, h))

        return one_snappers


    def get_right_bounds(self, x, y):
        right_bounds = []
        while x < self.W - self.half_alley:
            x += 1
            if self[x][y] == self.A:
                right_bounds.append(x)
        return right_bounds


    def get_bottom_bounds(self, x, y):
        bottom_bounds = []
        while y < self.H - self.half_alley:
            y += 1
            if self[x][y] == self.A:
                bottom_bounds.append(y)
        return bottom_bounds


    def get_unsnapped_shapes(self, x, y, target_area):
        lo = self.shape_min
        hi = None

        while 1:
            hi = target_area // lo
            if lo / hi >= 0.2:
                break  # maintain a certain minimum aspect ratio
            else:
                lo += 1

        unsnapped = []

        def enough_room(w, h):
            try:
                return self[x+w][y+h] in (self.C, self.A)
            except IndexError:
                return False

        for w in range(lo, hi+1):
            h = target_area // w
            if enough_room(w, h):
                unsnapped.append((w, h))

        return unsnapped


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
