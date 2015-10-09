#!/usr/bin/env python
import io
import random
import sys
import traceback
import itertools as it
import uuid
from math import ceil, sqrt

from geometry import Point, Segment


class NoPossibleShapes(Exception): pass
class TargetAreaTooSmall(Exception): pass
class UnevenAlleys(Exception): pass
class DoneAssigningIds(Exception): pass

class TilePlacementError(Exception):
    def __init__(self, *a):
        self.base_message = "Can't place '{}' at ({},{}).".format(*a[:3])
        Exception.__init__(self, *a)
    def __str__(self):
        return self.base_message + " " + self.message.format(*self.args)
    def __bytes__(self):
        return str(self).encode('utf8')

class BadTile(TilePlacementError):
    message = "Bad tile."

class OutOfBounds(TilePlacementError):
    message = "Out of bounds. Canvas size is ({3},{4})."

class AlreadyPlaced(TilePlacementError):
    message = "Already placed: '{3}'."


class MagnitudeMap(list):

    A = '-' # Alley
    B = '#' # Building
    C = ' ' # Canvas

    def __init__(self, canvas_size, sum_of_magnitudes=0, charset='-# ', alley_width=2,
            building_min=4, aspect_min=0.2):
        self.W, self.H = canvas_size
        if alley_width % 2 == 1: raise UnevenAlleys()
        self.alley_width = alley_width
        self.area = self.W * self.H
        self.remaining_area = (self.W - alley_width) * (self.H - alley_width)
        self.sum_of_magnitudes = sum_of_magnitudes
        self.remaining_magnitudes = sum_of_magnitudes
        self.charset = charset
        self.A, self.B, self.C = charset
        self.half_alley = alley_width // 2
        self.shape_min = building_min + alley_width
        self.aspect_min = aspect_min
        self.area_threshold = 1  # lowered automatically as space shrinks
        self.shapes = {}
        self.assignments = {}

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

    def __str__(self):
        out = []
        for y in range(self.H):
            for x in range(self.W):
                out.append(self[x][y])
            out.append('\n')
        return ''.join(out[:-1])

    def __bytes__(self):
        return str(self).encode('UTF-8')

    def to_svg(self, id='', offset_x=0, offset_y=0):
        fp = io.StringIO()
        print('    <svg id="{}" x="{}" y="{}" '
              'xmlns="http://www.w3.org/2000/svg">'.format(id, offset_x, offset_y), file=fp)
        for uid, (x, y, (w, h)) in self.shapes.items():
            print( '      <rect id="{}" x="{}px" y="{}px" width="{}px" height="{}px" />'
                   .format( self.assignments.get(uid, uid)
                          , x+self.half_alley
                          , y+self.half_alley
                          , w-self.alley_width
                          , h-self.alley_width
                           )
                 , file=fp
                  )
        print('    </svg>', file=fp)
        return fp.getvalue()

    def get_shape(self, uid):
        return self.shapes[uid]


    def load(self, u):
        self.remaining_area = self.W * self.H
        for y, row in enumerate(u.splitlines()):
            for x, char in enumerate(row):
                assert char in self.charset
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


    def add(self, magnitude, uid=None, shape_choice=None):

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

        # Also save it for the SVG renderer to use.
        uid = uid if uid else uuid.uuid4().hex
        self.shapes[uid] = (x, y, shape)

        # Decrement remaining_magnitudes.
        self.remaining_magnitudes -= magnitude

        # Recalculate area_threshold.
        self.area_threshold = self.remaining_area / self.area


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


    def assign_ids(self, pathways):
        """Given a pathways data structure, assign resources to shapes.

        The pathways data structure is a dictionary of {'pathway': ['resource-1', 'resource-2']}.

        The return structure should be {'pathway': [ ('shape-a', 'resource-1')
                                                   , ('shape-b', 'resource-2')
                                                    ]}

        The point of this method is to make the assignment in such a way as to
        have aesthetically pleasing pathways, ones that at the very least don't
        cross themselves.

        """

        # Flatten all resources into a single list (with predictable ordering).
        resources = list(it.chain(*[p[1] for p in sorted(pathways.items())]))

        # Give ourselves a way to find the pathway for a given resource.
        r2p = {}
        for k,v in pathways.items():
            for val in v:
              r2p[val] = k

        def get_center(shape):
            """Given a shape, return a Point for the center of it.
            """
            x,y, (w,h) = shape
            return Point(x + w/2, y + h/2)

        # Now let's explore the space of possibilities!
        space = []
        for permutation in it.permutations(sorted(self.shapes)):
            option = {k: [] for k in pathways}
            assignments = zip(permutation, resources)
            segments = []
            for i, assignment in enumerate(assignments):
                shape = self.shapes[assignment[0]]
                center = get_center(shape)

                if i == 0:      # First point: start a segment.
                    segments.append(Segment(center, center))
                elif i == 1:    # Second point: finish the first segment.
                    segments[0].point2 = center
                else:           # We're off and running: compare segments.
                    candidate = Segment(segments[-1].point2, center)
                    if i > 2:
                        bad = None
                        for segment in reversed(segments[:-1]):
                            if candidate.distance_from(segment) <= 1:
                                bad = True
                                break
                        if bad:
                            break
                    segments.append(candidate)

                option[r2p[assignment[1]]].append(assignment)
            else:
                space.append(option)
        self.assignments = random.choice(space)
        return space


def fake_data(N):
    return [random.randint(1, 20) for i in range(N)]


charsets = { 'ascii': '-# '
           , 'utf8': '\u2591\u2593 '
           , 'svg': 'SVG'  # hack
            }


def err(*a, **kw):
    print(file=sys.stderr, *a, **kw)


def main(topics, charset, width, height, alley_width, building_min):
    charset = charsets[charset]
    canvas_size = (width, height)
    street_width = alley_width * 10
    offset = street_width - alley_width
    big = [(topic_id, len(topic['subtopics'])) for topic_id, topic in topics.items()]
    big = fill_one( charset
                  , 'the whole thing'
                  , canvas_size
                  , big
                  , street_width
                  , building_min
                  , monkeys=False
                  , aspect_min=0.5
                   )
    print(big.to_svg(), file=open('output/big.svg', 'w+'))  # for debugging

    blocks = []
    for topic_id, topic in topics.items():
        small = []
        for subtopic in topic['subtopics'].values():
            for resource in subtopic['resources'].values():
                small.append((resource['id'], None))
        err()
        err(topic_id, '-' * (80 - len(topic_id) - 1))
        err()
        x, y, (w, h) = big.get_shape(topic_id)
        canvas_size = (w - offset, h - offset)
        blocks.append((topic_id, fill_one( charset
                                         , topic_id
                                         , canvas_size
                                         , small
                                         , alley_width
                                         , building_min
                                         , aspect_min=0.2
                                         , monkeys=True
                                          )))


    # Generate a combined SVG.
    # ========================

    half_W = big.W / 2
    half_H = big.H / 2
    rotated_side = lambda x: int(ceil(sqrt((x ** 2) / 2)))
    w = h = rotated_side(big.W) + rotated_side(big.H)
    half_w = w / 2
    half_h = h / 2

    fp = open('output/map.svg', 'w+')

    print('<svg width="{}px" height="{}px" '
          'xmlns="http://www.w3.org/2000/svg">'.format(w, h), file=fp)
    print('  <g transform="translate({} {}) rotate(45 {} {})">'
          .format(half_w - half_W, half_h - half_H, half_W, half_H), file=fp)

    offset = street_width // 2
    for uid, block in blocks:
        x, y, shape = big.shapes[uid]
        subtopics = topics[uid]['subtopics'].values()
        pathways = {s['id']: s['dag']['names'] for s in subtopics}
        block.assign_ids(pathways)
        print(block.to_svg(uid, x + offset, y + offset), file=fp)

    print('  </g>', file=fp)
    print('</svg>', file=fp)


def fill_one(charset, name, canvas_size, magnitudes, alley_width, building_min, monkeys, **kw):
    i = 0
    mfunc = (lambda m: random.randint(3, 10)) if monkeys else (lambda m: m)
    while 1:
        i += 1
        err('Iteration:', i)

        magnitudes = [(uid, mfunc(m)) for uid, m in magnitudes]
        nmagnitudes = len(magnitudes)
        smagnitudes = sum([m[1] for m in magnitudes])

        nplaced = 0
        nremaining = nmagnitudes
        m = MagnitudeMap(canvas_size=canvas_size, sum_of_magnitudes=smagnitudes, charset=charset,
                         alley_width=alley_width, building_min=building_min, **kw)
        try:
            for _, magnitude in magnitudes:
                m.add(magnitude)
                nplaced += 1
                nremaining -= 1
        except:
            tb = traceback.format_exc()
        else:
            tb = ''

        err()
        err("Placed {} out of {} magnitudes for {}.".format(nplaced, len(magnitudes), name))
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

        if nremaining == 0 and m.remaining_area == 0:
            break
    return m


if __name__ == '__main__':
    import argparse, json

    parser = argparse.ArgumentParser(description='Generate a CaaC map.')
    parser.add_argument('input', help='the name of an input file in json format')
    parser.add_argument('--charset', '-c', default='utf8', help='the character set to use',
                        choices=sorted(charsets.keys()))
    parser.add_argument('--width', '-W', default=128, type=int, help='the width of the canvas')
    parser.add_argument('--height', '-H', default=128, type=int, help='the height of the canvas')
    parser.add_argument('--alley_width', '-a', default=6, type=int, help='the width of the alleys')
    parser.add_argument('--building_min', '-b', default=10, type=int,
                        help='the minimum width of the blocks')

    args = parser.parse_args()
    topics = json.load(open(args.input))
    args.__dict__.pop('input')
    main(topics, **args.__dict__)
