from __future__ import absolute_import, division, print_function, unicode_literals

import itertools as it

from geometry import Point, Segment


logfile = open('backtrack.log', 'w+')
def log(*a, **kw):
    msg, a = (a[0], a[1:]) if len(a) else ('', a)
    kw['file'] = logfile
    print(msg.ljust(24), *a, **kw)


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
            log("Rejecting!")
            return True
        segments.append(segment)
    return False

def accept(P, c):
    return len(flatten(c)) == P.n

def output(P, c):
    P.solutions.append({k:v[:] for k,v in c.items()})  # be sure to copy it!

def first(P, c):
    if len(P.indices) == P.n:
        return None  # base case
    elif not P.indices:
        s,r = (0,0)
    else:
        s,r = P.indices[-1]
        s += 1
        r += 1
        if s == P.n: s = 0
        if r == P.n: r = 0
    P.indices.append((s,r))
    shape_id, resource_id = P.shapes[s], P.resources[r]
    c[P.r2p[resource_id]].append((shape_id, resource_id))
    return c

def next(P, sibling):
    if not P.indices:
        pass
    s,r = P.indices[-1]
    s += 1
    if s == P.n:
        s = 0
        r += 1
        if r == P.n:
            return None  # base case
    P.indices[-1] = (s, r)
    shape_id, resource_id = P.shapes[s], P.resources[r]
    sibling[P.r2p[resource_id]][-1] = (shape_id, resource_id)
    return sibling

def backtrack(P, c):
    log("Called with:", c)
    if reject(P, c): return
    log("Not rejected.")
    if accept(P, c): output(P, c)
    log("Accepted?", P.solutions)
    s = first(P, c)
    log("First sibling:", s)
    while s:
        log("Recursing ...")
        log()
        backtrack(P, s)
        log("Recursed.")
        s = next(P, s)
        log("Next sibling:", s)

    # Clean up mutated objects.
    log("Cleaning up.")
    if P.indices: _,r = P.indices.pop()
    if P.r2p:
        pathway_id = P.r2p[P.resources[r]]
        if s: s[pathway_id].pop()
        if P.p2s[pathway_id]: P.p2s[pathway_id].pop()
