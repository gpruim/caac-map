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
    latest_pathway_assignment = None

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
        self.segments = {k:[] for k in pathways}

        # Maintain indices into shapes and resources for the current node while backtracking.
        self.pairs = []  # pairs of (shape_index, resource_index)
        self.shape_pool = set(range(self.n))
        self.resource_pool = set(range(self.n))
        self.siblings = []  # stack of siblings generators

        # We'll accumulate solutions into a list.
        self.solutions = []

        # Logfile!
        self.logfile = open('problem.log', 'w+')
        self.loglines = 0


    def log(self, *a, **kw):
        self.loglines += 1
        msg, a = (a[0], a[1:]) if len(a) else ('', a)
        kw['file'] = self.logfile
        print('{:>2} {} {} {} {}'
              .format( self.loglines
                     , '| '*self.depth
                     , msg.ljust(24-(2*self.depth))
                     , len(self.siblings)
                     , len(self.solutions)
                      ), *a, **kw)


def solve(shapes, pathways):
    problem = Problem(shapes, pathways)
    backtrack(problem, root(problem))

    # XXX Now do goofy deduplication. We should be able to prune these or
    # something during backtracking.

    solutions = []
    for solution in problem.solutions:
        for d in solutions:
            if solution == d:
                break
        else:
            solutions.append(solution)

    return solutions


# Backtracking Algorithm
# ======================
# https://en.wikipedia.org/wiki/Backtracking

def root(P):
    return {k:[] for k in P.pathways}

def reject(P, c):
    if not P.pairs:
        assert flatten(c) == tuple()  # first case, root
        return False

    s,r = P.pairs[-1]
    shape_id, resource_id = P.shapes[s], P.resources[r]


    # Check for pathway containment.
    # ==============================

    if P.r2p[resource_id] != P.latest_pathway_assignment:
        P.log('reject', "{} not in {}!".format(resource_id, P.r2p[resource_id]))
        return True


    # Check for edge crossings.
    # =========================

    shape = P.s2shape[shape_id]
    center = get_center(shape)
    pathway_id = P.r2p[resource_id]
    segments = P.segments[pathway_id]
    nsegments = len(segments)

    if nsegments == 0:      # First point: start a segment.
        segments.append(Segment(center, center))
    elif nsegments == 1:    # Second point: finish the first segment.
        segments[0].point2 = center
    else:                   # We're off and running: validate segments.
        segment = get_valid_segment(segments, center)
        if segment is None:
            P.log('reject', 'cross')
            return True
        segments.append(segment)
    return False

def accept(P, c):
    return len(flatten(c)) == P.n

def output(P, c):
    P.solutions.append({k:v[:] for k,v in c.items()})  # be sure to copy it!
    P.log('a solution!', sorted(P.solutions[-1].items()))

def first(P, c):
    P.siblings.append(it.product(sorted(P.shape_pool), sorted(P.resource_pool)))
    try:
        s,r = next(P.siblings[-1])
    except StopIteration:
        P.siblings.pop()  # this is a null iterator, throw it away!
        return None  # base case
    P.shape_pool.remove(s)
    P.resource_pool.remove(r)
    P.pairs.append((s,r))
    shape_id, resource_id = P.shapes[s], P.resources[r]
    pathway_id = P.r2p[resource_id]
    c[pathway_id].append((shape_id, resource_id))
    P.latest_pathway_assignment = pathway_id
    P.log('\ append {}'.format((s,r)), P.pairs, sorted(c.items()))
    return c

def next_(P, sibling):
    if not P.pairs:
        return None  # root case

    s,r = P.pairs[-1]
    P.log('| seek {}'.format((s,r)), P.pairs)
    P.shape_pool.add(s)
    P.resource_pool.add(r)

    old_pathway_id = P.r2p[P.resources[r]]
    old_pathway = sibling[old_pathway_id]

    try:
        s,r = next(P.siblings[-1])
    except StopIteration:
        return None  # base case

    P.shape_pool.remove(s)
    P.resource_pool.remove(r)
    P.pairs[-1] = (s,r)
    shape_id, resource_id = P.shapes[s], P.resources[r]

    new_pathway_id = P.latest_pathway_assignment = P.r2p[resource_id]
    new_pathway = sibling[new_pathway_id]

    if new_pathway is old_pathway:
        new_pathway[-1] = (shape_id, resource_id)
    else:
        old_pathway.pop()
        new_pathway.append((shape_id, resource_id))

    P.log('\ set {}'.format((s,r)), P.pairs, sorted(sibling.items()))
    return sibling

def clean_up(P, c):
    """Clean up mutated objects. This is an extension to Wikipedia's backtrack algorithm.
    """
    if not P.pairs: return  # root case
    P.siblings.pop()
    s,r = P.pairs.pop()
    P.shape_pool.add(s)
    P.resource_pool.add(r)
    if P.r2p:
        pathway_id = P.r2p[P.resources[r]]
        if c and c[pathway_id]:
            c[pathway_id].pop()
        if P.segments[pathway_id]:
            P.log('popping segment for', pathway_id)
            P.segments[pathway_id].pop()
    P.log('\ pop {}'.format((s,r)), P.pairs, sorted(c.items()))

def backtrack(P, c):
    P.ncalls += 1
    P.depth += 1
    if reject(P, c): return
    if accept(P, c): output(P, c)
    s = first(P, c)
    while s:
        backtrack(P, s)
        s = next_(P, s)
    clean_up(P, c)
    P.depth -= 1
