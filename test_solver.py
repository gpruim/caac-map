import pathways_solver as ps

# Problem

def test_we_can_express_an_empty_problem():
    assert ps.Problem({}, {}).solutions == []


# solve

def test_solve_solves_pathways():
    assert ps.solve({}, {}) == [{}]
