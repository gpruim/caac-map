#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import random


class NoPossibleShapes(Exception): pass
class TargetAreaTooSmall(Exception): pass
class UnevenAlleys(Exception): pass

class TilePlacementError(Exception):
    def __init__(self, *a):
        self.base_message = "Can't place '{}' at ({},{}).".format(*a[:3])
        Exception.__init__(self, *a)
    def __unicode__(self):
        return self.base_message + " " + self.message.format(*self.args)
    __str__ = __unicode__

class BadTile(TilePlacementError):
    message = "Bad tile."

class OutOfBounds(TilePlacementError):
    message = "Out of bounds. Canvas size is ({3},{4})."

class AlreadyPlaced(TilePlacementError):
    message = "Already placed: '{3}'."


class MagnitudeMap(list):

    A = '-' # Alley
    B = '#' # Block/Building
    C = ' ' # Canvas

    def __init__(self, canvas_size, sum_of_magnitudes=0, chars='-# ', alley_width=2, block_min=4,
            aspect_min=0.2, area_threshold=1):
        self.W, self.H = canvas_size
        if alley_width % 2 == 1: raise UnevenAlleys()
        self.alley_width = alley_width
        self.area = self.W * self.H
        self.remaining_area = (self.W - alley_width) * (self.H - alley_width)
        self.sum_of_magnitudes = sum_of_magnitudes
        self.remaining_magnitudes = sum_of_magnitudes
        self.chars = chars
        self.A, self.B, self.C = chars
        self.half_alley = alley_width // 2
        self.shape_min = block_min + alley_width
        self.aspect_min = aspect_min
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


    def load(self, u):
        self.remaining_area = self.W * self.H
        for y, row in enumerate(u.splitlines()):
            for x, char in enumerate(row):
                assert char in self.chars
                self[x][y] = char
                if char != self.C:
                    self.remaining_area -= 1


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

        # Try to find a nice fit.
        shapes = self.get_snapped_shapes(x, y, target_area)
        if not shapes:
            shapes = self.get_unsnapped_shapes(x, y, target_area)
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
        if tile not in (self.A, self.B):
            raise BadTile(tile, x, y)
        try:
            if x < 0 or y < 0:  # Beware of negative indexing! We don't want it.
                raise IndexError
            if self[x][y] != self.C:
                raise AlreadyPlaced(tile, x, y, self[x][y])
        except IndexError:
            raise OutOfBounds(tile, x, y, self.W, self.H)
        self[x][y] = tile
        self.remaining_area -= 1


    def draw_shape_at(self, shape, x, y):
        w, h = [dimension - self.alley_width for dimension in shape]
        x = x + self.half_alley
        y = y + self.half_alley
        for x_ in range(x, x+w):
            for y_ in range(y, y+h):
                self.place_tile(self.B, x_, y_)
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


    def too_small(self, w, h):
        return w < self.shape_min or h < self.shape_min

    def too_skinny(self, w, h):
        return min(w, h) / max(w, h) < self.aspect_min

    def enough_room(self, w, h, x, y):
        for x_ in range(x, x+w):        # check first row
            if self[x_][y] != self.C:
                return False
        for y_ in range(y, y+h):        # check final col
            if self[x+w-1][y_] != self.C:
                return False
        return True

    def bad_shape_for(self, shape, x, y):
        w, h = shape
        return self.too_small(w, h) or self.too_skinny(w, h) or not self.enough_room(w, h, x, y)


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

        for right_bound in right_bounds:
            for bottom_bound in bottom_bounds:
                w = right_bound - x
                h = bottom_bound - y
                if self.bad_shape_for((w, h), x, y):
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

        def enough_remaining(x, y):
            try:
                return self[x][y] == self.C
            except IndexError:
                return False

        for right_bound in right_bounds:
            w = right_bound - x
            h = target_area // w
            while h and not enough_remaining(x, y + h-1 + self.shape_min):
                h -= 1
            if not self.bad_shape_for((w, h), x, y):
                one_snappers.append((w, h))

        for bottom_bound in bottom_bounds:
            h = bottom_bound - y
            w = target_area // h
            while w and not enough_remaining(x + w-1 + self.shape_min, y):
                w -= 1
            if not self.bad_shape_for((w, h), x, y):
                one_snappers.append((w, h))

        return one_snappers


    def get_right_bounds(self, x, y):
        return self._get_bounds(self.W, x, y, lambda a,b: self[a][b])

    def get_bottom_bounds(self, x, y):
        return self._get_bounds(self.H, y, x, lambda a,b: self[b][a])

    def _get_bounds(self, D, a, b, tile):
        bounds = set()
        into_alley = 0
        b_ = b - self.half_alley - 1
        while a < D - self.half_alley:
            a += 1

            # hard bound
            if tile(a, b) == self.A:
                bounds.add(a)
                break

            # soft bounds
            if b_ < self.half_alley:
                continue
            c = tile(a, b_)
            if c == self.A:
                into_alley += 1
                if into_alley == self.half_alley:
                    bounds.add(a+1)
            elif c == self.B:
                into_alley = 0

        return sorted(list(bounds))


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


def fake_data(N):
    return [random.randint(1, 10) for i in range(N)]


if __name__ == '__main__':
    import sys
    import traceback

    charsets = { 'terminal': '\u2591\u2593 '
               , 'web': ( '<div class="tile A"></div>'
                        , '<div class="tile B"></div>'
                        , '<div class="tile C"></div>'
                         )
                }

    args = dict(zip(['charset', 'W', 'H', 'N'], sys.argv[1:2] + map(int, sys.argv[2:])))
    charset = charsets[args.get('charset', 'terminal')]
    W = args.get('W', 128)
    H = args.get('H', 128)
    N = args.get('N', 40)

    magnitudes = fake_data(N)
    m = MagnitudeMap(canvas_size=(W, H), sum_of_magnitudes=sum(magnitudes), chars=charset)
    try:
        i = 0
        N = len(magnitudes)
        for magnitude in magnitudes:
            i += 1
            m.add(magnitude)
    except:
        tb = traceback.format_exc()
    else:
        tb = ''

    if m.chars == charsets['web']:
        print("""
        <style>
            body {{ margin: 0; padding: 0; background: #CCC; }}
            div.wrapper {{ width: {0}px; height: {1}px; margin: 100px auto; }}
            div.tile {{ width:4px; height: 4px; float: left; }}
            div.A {{ background: #FFFFFF; }}
            div.B {{ background: #0099FF; }}
            div.C {{ background: transparent; }}
        </style>
        <div class="wrapper">
        """.format(m.W*4, m.H*4, (m.H*4) // 2))
        print(m)
        print("</div>")
    else:
        print(m)

    err = lambda *a, **kw: print(file=sys.stderr, *a, **kw)
    err()
    err("Placed {} out of {} magnitudes.".format(i, N))
    err( "Sum of remaining magnitudes: {} / {} ({:.1f}%)".format(
         m.remaining_magnitudes
       , m.sum_of_magnitudes
       , (m.remaining_magnitudes / m.sum_of_magnitudes) * 100
        ))
    err( "Remaining area: {} / {} ({:.1f}%)".format(
         m.remaining_area
       , m.area
       , (m.remaining_area / m.area) * 100
        ))
    if tb:
        err()
        err(tb)
