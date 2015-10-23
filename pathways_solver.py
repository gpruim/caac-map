from __future__ import absolute_import, division, print_function, unicode_literals

import itertools as it
from operator import mul
from functools import reduce
from math import inf

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


square = lambda x: x ** 2

def count_possible_solutions(level):
    return reduce(mul, map(square, range(1, level)), 1)

def count_nodes(level):
    return 1 + sum(reduce(mul, map(square, range(v, level)), 1) for v in range(1, level))


class FirstSolutionFound(Exception): pass
class NoSolutionFound(Exception): pass


class Problem(object):

    depth = -1
    latest_pathway_assignment = None

    def __init__(self, shapes, pathways, take_first=False, max_nodes=inf):
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
        self.take_first = take_first    # whether to raise after the first solution is found
        self.max_nodes = max_nodes      # max number of nodes to touch before giving up
        self.resources = flatten(pathways)
        #XXX bad data! assert len(self.resources) == self.nlevels, (self.resources, self.nlevels, shapes, pathways)

        nlevels = len(self.shapes)
        self.stats = { 'ncalls': 0
                     , 'nlevels': nlevels
                     , 'nsolutions': 0
                     , 'npossible_solutions': count_possible_solutions(nlevels)
                     , 'nnodes': count_nodes(nlevels)
                      }

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
        self.shape_pool = set(range(nlevels))
        self.resource_pool = set(range(nlevels))
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
        kw['flush'] = True
        print('{:>2} {} {} {} {}'
              .format( self.loglines
                     , '| '*self.depth
                     , msg.ljust(24-(2*self.depth))
                     , len(self.siblings)
                     , len(self.solutions)
                      ), *a, **kw)


def solve(shapes, pathways, take_first=False, max_nodes=inf):
    problem = Problem(shapes, pathways, take_first, max_nodes)
    try:
        backtrack(problem, root(problem))
    except FirstSolutionFound as exc:
        solution = exc.args[0]
        return [solution]

    if not problem.solutions:
        raise NoSolutionFound()

    # XXX Now do goofy deduplication. We should be able to prune these or
    # something during backtracking. We have duplicates because of the way we
    # constrain pathway assignment based on resource id, so that both [(0,0),
    # (1,1)] and [(1,1), (0,0)] result in the same solution if r=0 and 1
    # dereference to resources that are in different pathways.

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


    # Check for edge crossings.
    # =========================

    pathway_id = P.r2p[resource_id]
    segments = P.segments[pathway_id]

    if len(segments) > 2:
        last_segment = segments[-1]
        for earlier_segment in reversed(segments[:-2]):
            if last_segment.distance_from(earlier_segment) <= 1:
                return True
    return False

def accept(P, c):
    n = P.stats['nlevels']
    if not n:
        return True

    nassigned = len(flatten(c))
    threshold = 1 - (P.stats['ncalls'] / P.max_nodes)
    if nassigned / n >= threshold:
        print("Accepting a {} / {} = {:.0f}% solution after {} nodes."
              .format(nassigned, n, (nassigned/n) * 100, P.stats['ncalls']))
        return True

    return False

def output(P, c):
    solution = {k:v[:] for k,v in c.items()}  # be sure to copy it!
    P.stats['nsolutions'] += 1
    if P.take_first:
        raise FirstSolutionFound(solution)
    else:
        P.solutions.append(solution)

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
    pathway_id = P.latest_pathway_assignment = P.r2p[resource_id]
    c[pathway_id].append((shape_id, resource_id))
    center = get_center(P.s2shape[shape_id])
    segments = P.segments[pathway_id]

    if not segments:                                    # First point: start a segment.
        segments.append(Segment(center, center))
    elif segments[-1].point1 is segments[-1].point2:    # Second point: finish the first segment.
        segments[-1].point2 = center
    else:                                               # We're off and running: validate segments.
        previous_point = segments[-1].point2
        segments.append(Segment(previous_point, center))

    return c

def next_(P, sibling):
    if not P.pairs:
        return None  # root case

    s,r = P.pairs[-1]
    P.shape_pool.add(s)
    P.resource_pool.add(r)

    _old = P.r2p[P.resources[r]]
    old_pathway = sibling[_old]
    old_segments = P.segments[_old]

    try:
        s,r = next(P.siblings[-1])
    except StopIteration:
        return None  # base case

    P.shape_pool.remove(s)
    P.resource_pool.remove(r)
    P.pairs[-1] = (s,r)
    shape_id, resource_id = P.shapes[s], P.resources[r]
    center = get_center(P.s2shape[shape_id])

    _new = P.latest_pathway_assignment = P.r2p[resource_id]
    new_pathway = sibling[_new]
    new_segments = P.segments[_new]

    if new_pathway is old_pathway:      # Same pathway, overwrite.
        new_pathway[-1] = (shape_id, resource_id)
        if new_segments:
            new_segments[-1].point2 = center
        else:
            new_segments.append(Segment(center, center))
    else:                               # Different pathway, remove there and add here.
        # Remove old ...
        old_pathway.pop()
        if not old_segments:
            pass
        elif len(old_segments) == 1 and not (old_segments[0].point2 is old_segments[0].point1):
            old_segments[0].point2 = old_segments[0].point1
        else:
            old_segments.pop()

        # Add new ...
        new_pathway.append((shape_id, resource_id))
        if not new_segments:
            pass
        elif new_segments[-1].point1 is new_segments[-1].point2:
            # Second point: finish the first segment.
            new_segments[-1].point2 = center
        else:
            # We're off and running: validate segments.
            previous_point = new_segments[-1].point2
            new_segments.append(Segment(previous_point, center))

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
            P.segments[pathway_id].pop()

def backtrack(P, c):
    P.depth += 1
    P.stats['ncalls'] += 1
    if P.stats['ncalls'] % 10000 == 0:
        print('{depth} / {nlevels} | {ncalls} / {nnodes} | {nsolutions} / {npossible_solutions}'
              .format(depth=P.depth, **P.stats))
    if reject(P, c):
        P.stats['npossible_solutions'] -= count_possible_solutions(P.stats['nlevels'] - P.depth)
        P.stats['nnodes'] -= count_nodes(P.stats['nlevels'] - P.depth)
        P.depth -= 1
        return
    if accept(P, c): output(P, c)
    s = first(P, c)
    while s:
        backtrack(P, s)
        s = next_(P, s)
    clean_up(P, c)
    P.depth -= 1
