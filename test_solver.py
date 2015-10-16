import pathways_solver as ps


# Problem

def test_we_can_express_an_empty_problem():
    assert ps.Problem({}, {}).solutions == []


# solve

def test_solve_solves_pathways():
    assert ps.solve({}, {}) == [{}]


# next

def test_next_sibling_properly_identifies_base_case():
    P = ps.Problem({'a': None, 'b': None}, {'foo': ['x', 'y']})
    P.indices = [(0,0)]
    s = {'foo': [('a', 'x'), ('b', 'y')]}
    assert ps.next(P, s) == None
