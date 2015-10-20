import pathways_solver as ps


def test_count_possible_solutions_counts_possible_solutions():
    assert ps.count_possible_solutions(1) == 1
    assert ps.count_possible_solutions(2) == 1
    assert ps.count_possible_solutions(3) == 4
    assert ps.count_possible_solutions(4) == 36
    assert ps.count_possible_solutions(5) == 576
    assert ps.count_possible_solutions(6) == 14400
    assert ps.count_possible_solutions(7) == 518400

def test_count_nodes_counts_nodes():
    assert ps.count_nodes(1) == 1
    assert ps.count_nodes(2) == 2
    assert ps.count_nodes(3) == 9
    assert ps.count_nodes(4) == 82
    assert ps.count_nodes(5) == 1313
    assert ps.count_nodes(6) == 32826


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
    assert ps.next_(P, s) == None
