from __future__ import absolute_import, division, print_function, unicode_literals

import itertools as it

from geometry import Point, Segment


def flatten(pathways):
    """Flatten all resources into a single sequence (with predictable ordering).

    This assumes that resource ids are unique across pathways, of course.

    """
    return tuple(it.chain(*[p[1] for p in sorted(pathways.items())]))

def get_center(shape):
    """Given a shape, return a Point for the center of it.
    """
    x,y, (w,h) = shape
    return Point(x + w/2, y + h/2)

def get_valid_segment(segments, point):
    """Given a list of segments and a point, return a segment or None.
    """
    candidate = Segment(segments[-1].point2, point)
    for segment in reversed(segments[:-1]):
        if candidate.distance_from(segment) <= 1:
            return None
    return candidate


class Problem(object):

    depth = -1
    ncalls = 0

    def __init__(self, shapes, pathways):
        """Instantiate a pathways assignment problem.

        The problem definition is given in a shapes dictionary, mapping shape
        id to shape definition, and a pathways dictionary, which has this
        structure:

            {'pathway': ['resource-1', 'resource-2']}

        The return structure should be:

            {'pathway': [ ('shape-a', 'resource-1'), ('shape-b', 'resource-2')]}

        The point of this exercise is to make the assignment in such a way as
        to have aesthetically pleasing pathways, ones that at the very least
        don't cross themselves.

        """
        self.shapes = tuple(sorted(shapes))
        self.pathways = pathways
        self.resources = flatten(pathways)
        self.n = len(self.shapes)
        assert len(self.resources) == self.n

        # Make sure we can access shape definitions by id.
        self.s2shape = shapes

        # Give ourselves a way to find the pathway for a given resource.
        self.r2p = {}
        for k,v in pathways.items():
            for val in v:
              self.r2p[val] = k

        # And let's maintain a list of segments for each pathway.
        self.p2s = {k:[] for k in pathways}

        # Maintain indices into shapes and resources for the current node while backtracking.
        self.indices = []  # pairs of (shape_index, resource_index) per level

        # We'll accumulate solutions into a list.
        self.solutions = []

        # Logfile!
        self.logfile = open('problem.log', 'w+')
        self.loglines = 0


    def log(self, *a, **kw):
        self.loglines += 1
        msg, a = (a[0], a[1:]) if len(a) else ('', a)
        kw['file'] = self.logfile
        print('{:>2} {}{}'.format( self.loglines
                                 , '| '*self.depth
                                 , msg.ljust(24-(2*self.depth)))
                                 , *a
                                 , **kw
                                  )

    def clean_up(self, s):
        """Clean up mutated objects.
        """
        if self.indices:
            _,r = self.indices.pop()
            self.log('\ pop {}'.format((_,r)), self.indices)
            if self.r2p:
                pathway_id = self.r2p[self.resources[r]]
                if s:
                    s[pathway_id].pop()
                if self.p2s[pathway_id]:
                    self.p2s[pathway_id].pop()


def solve(shapes, pathways):
    problem = Problem(shapes, pathways)
    backtrack(problem, root(problem))
    return problem.solutions


# Backtracking Algorithm
# ======================
# https://en.wikipedia.org/wiki/Backtracking

def root(P):
    return {k:[] for k in P.pathways}

def reject(P, c):
    if not P.indices:
        assert flatten(c) == tuple()  # first case, root
        return False

    s,r = P.indices[-1]
    shape_id, resource_id = P.shapes[s], P.resources[r]
    shape = P.s2shape[shape_id]
    center = get_center(shape)
    pathway_id = P.r2p[resource_id]
    segments = P.p2s[pathway_id]
    nsegments = len(segments)

    if nsegments == 0:      # First point: start a segment.
        segments.append(Segment(center, center))
    elif nsegments == 1:    # Second point: finish the first segment.
        segments[0].point2 = center
    else:                   # We're off and running: validate segments.
        segment = get_valid_segment(segments, center)
        if segment is None:
            P.log("Rejecting!")
            return True
        segments.append(segment)
    return False

def accept(P, c):
    return len(flatten(c)) == P.n

def output(P, c):
    P.solutions.append({k:v[:] for k,v in c.items()})  # be sure to copy it!

def first(P, c):
    #P.log("first", P.indices)
    if len(P.indices) == P.n:
        return None  # base case
    elif not P.indices:
        s,r = (0,0)  # root case
    else:
        s,r = P.indices[-1]
        s += 1
        r += 1
        if s == P.n: s = 0
        if r == P.n: r = 0
    P.indices.append((s,r))
    P.log('\ append {}'.format((s,r)), P.indices)
    shape_id, resource_id = P.shapes[s], P.resources[r]
    c[P.r2p[resource_id]].append((shape_id, resource_id))
    return c

def next(P, sibling):
    if not P.indices:
        return None  # base case
    s,r = P.indices[-1]
    P.log('| seek {}'.format((s,r)), P.indices)
    s += 1
    if s == P.n:
        s = 0
        r += 1
        if r == P.n:
            return None  # base case
    P.indices[-1] = (s,r)
    P.log('\ set {}'.format((s,r)), P.indices)
    shape_id, resource_id = P.shapes[s], P.resources[r]
    #P.log("next", shape_id, resource_id)
    sibling[P.r2p[resource_id]][-1] = (shape_id, resource_id)
    return sibling

def backtrack(P, c):
    P.ncalls += 1
    P.depth += 1
    #P.log("Call #{}".format(P.ncalls), c)
    if reject(P, c): return
    if accept(P, c): output(P, c)
    #P.log("Solutions:", len(P.solutions))
    s = first(P, c)
    #P.log("First child:", s)
    while s:
        #P.log()
        backtrack(P, s)
        #P.log()
        #P.log("Prev sibling:", s)
        s = next(P, s)
        #P.log("Next sibling:", s)
    #P.log("Cleaning up.")
    P.clean_up(c)
    P.depth -= 1
