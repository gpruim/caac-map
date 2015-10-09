import genmap
from pytest import raises


def test_map_can_draw_an_empty_canvas():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=0)
    assert str(m) == """\
----------------
-              -
-              -
-              -
-              -
-              -
-              -
----------------"""


def test_map_can_draw_an_empty_canvas_with_different_size():
    m = genmap.MagnitudeMap(canvas_size=(40, 16), alley_width=4)
    assert str(m) == """\
----------------------------------------
----------------------------------------
--                                    --
--                                    --
--                                    --
--                                    --
--                                    --
--                                    --
--                                    --
--                                    --
--                                    --
--                                    --
--                                    --
--                                    --
----------------------------------------
----------------------------------------"""


def test_map_requires_alleys_to_be_even_widths():
    genmap.MagnitudeMap(canvas_size=(16, 8), alley_width=2)
    with raises(genmap.UnevenAlleys):
        genmap.MagnitudeMap(canvas_size=(16, 8), alley_width=3)
    genmap.MagnitudeMap(canvas_size=(16, 8), alley_width=4)


def test_map_can_be_loaded_from_str():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    u = """\
----------------
-              -
- ### # #   #  -
-  #  # ## ##  -
-  #  # # # #  -
-  #  # #   #  -
-              -
----------------"""
    m.load(u)
    assert str(m) == u


def test_load_checks_for_character_fitness():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    u = """\
----------------
-              -
- ### # #   #  -
-  #  # ## ##  -
-  #  # # $ #  -
-  #  # #   #  -
-              -
----------------"""
    with raises(AssertionError):
        m.load(u)

# place_tile - pt

def test_pt_places_tile():
    m = genmap.MagnitudeMap(canvas_size=(16,8))
    m.place_tile(m.B, 3, 4)
    assert str(m) == """\
----------------
-              -
-              -
-              -
-  #           -
-              -
-              -
----------------"""

def test_pt_rejects_bad_tile():
    m = genmap.MagnitudeMap(canvas_size=(16,8))
    with raises(genmap.BadTile) as err:
        m.place_tile('$', 3, 4)
    assert str(err.value) == "Can't place '$' at (3,4). Bad tile."

def test_pt_rejects_clobbering_tile():
    m = genmap.MagnitudeMap(canvas_size=(16,8))
    with raises(genmap.AlreadyPlaced) as err:
        m.place_tile('#', 0, 0)
    assert str(err.value) == "Can't place '#' at (0,0). Already placed: '-'."

def test_pt_rejects_out_of_bounds_tile():
    m = genmap.MagnitudeMap(canvas_size=(16,8))
    with raises(genmap.OutOfBounds) as err:
        m.place_tile('#', -1, 16)
    assert str(err.value) == "Can't place '#' at (-1,16). Out of bounds. " \
                                 "Canvas size is (16,8)."

    m[0][0] = ' '
    assert m[0][0] == ' '
    raises(genmap.OutOfBounds, m.place_tile, '#', 0, -1)
    raises(genmap.OutOfBounds, m.place_tile, '#', -1, 0)
    m.place_tile('#', 0, 0)
    assert m[0][0] == '#'

    m[15][0] = ' '
    assert m[15][0] == ' '
    raises(genmap.OutOfBounds, m.place_tile, '#', 15, -1)
    raises(genmap.OutOfBounds, m.place_tile, '#', 16, 0)
    m.place_tile('#', 15, 0)
    assert m[15][0] == '#'

    m[0][7] = ' '
    assert m[0][7] == ' '
    raises(genmap.OutOfBounds, m.place_tile, '#', 0, 8)
    raises(genmap.OutOfBounds, m.place_tile, '#', -1, 7)
    m.place_tile('#', 0, 7)
    assert m[0][7] == '#'

    m[15][7] = ' '
    assert m[15][7] == ' '
    raises(genmap.OutOfBounds, m.place_tile, '#', 15, 8)
    raises(genmap.OutOfBounds, m.place_tile, '#', 16, 7)
    m.place_tile('#', 15, 7)
    assert m[15][7] == '#'


# find_starting_corner - fsc

def test_fsc_finds_starting_corner():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    assert m.find_starting_corner() == (1, 1)


# determine_target_area - dta

def test_dta_determines_target_area():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=10)
    assert m.determine_target_area(10) == 84

def test_dta_prorates_based_on_sum_of_magnitudes():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=20)
    assert m.determine_target_area(10) == 42

def test_dta_varies_with_canvas_size():
    m = genmap.MagnitudeMap(canvas_size=(16, 16), sum_of_magnitudes=20)
    assert m.determine_target_area(10) == 98

def test_dta_enforces_lower_bound():
    m = genmap.MagnitudeMap(canvas_size=(14, 14), sum_of_magnitudes=8, building_min=4)
    with raises(genmap.TargetAreaTooSmall):
        m.determine_target_area(1)
    m.determine_target_area(2)


# get_right_bounds - grb

def test_grb_gets_right_bounds():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    assert m.get_right_bounds(1, 1) == [15]

def test_grb_stops_at_first_hard_bound():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    m.load("""\
----------------
-     -        -
-              -
-              -
-              -
-              -
-              -
----------------""")
    assert m.get_right_bounds(1, 1) == [6]

def test_grb_finds_soft_and_hard_bounds():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=1)
    m.load("""\
----------------
----------------
--####--######--
----------------
-              -
-              -
-              -
----------------""")
    assert m.get_right_bounds(1, 4) == [7, 15]

def test_grb_finds_soft_bound_with_some_empty_canvas():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=1)
    m.load("""\
----------------
-------        -
--####-        -
-------        -
-              -
-              -
-              -
----------------""")
    assert m.get_right_bounds(1, 4) == [7, 15]

def test_grb_works_with_different_alley_width_shhhhhh_dont_tell_tim():
    m = genmap.MagnitudeMap(canvas_size=(24, 18), alley_width=4, building_min=1)
    m.load("""\
------------------------
------------------------
------------------------
------------------------
----######----######----
----######----######----
----######----######----
------------------------
------------------------
--                    --
--                    --
--                    --
--                    --
--                    --
--                    --
--                    --
------------------------
------------------------""")
    assert m.find_starting_corner() == (2, 9)
    assert m.get_right_bounds(2, 9) == [12, 22]


# get_bottom_bounds - gbb

def test_gbb_gets_bottom_bounds():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    assert m.get_bottom_bounds(1, 1) == [7]

def test_gbb_stops_at_first_hard_bound():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    m.load("""\
----------------
-              -
-              -
-              -
--             -
-              -
-              -
----------------""")
    assert m.get_bottom_bounds(1, 1) == [4]

def test_gbb_finds_soft_and_hard_bounds():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=1)
    m.load("""\
----------------
-------        -
--####-        -
-------        -
-------        -
--####-        -
-------        -
----------------""")
    assert m.get_bottom_bounds(7, 1) == [4, 7]

def test_gbb_finds_soft_bound_with_some_empty_canvas():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=1)
    m.load("""\
----------------
-------        -
--####-        -
-------        -
-              -
-              -
-              -
----------------""")
    assert m.get_bottom_bounds(7, 1) == [4, 7]

def test_gbb_works_with_different_alley_width_shhhhhh_dont_tell_tim():
    m = genmap.MagnitudeMap(canvas_size=(24, 18), alley_width=4, building_min=1)
    m.load("""\
------------------------
------------------------
------------          --
------------          --
----######--          --
----######--          --
----######--          --
------------          --
------------          --
------------          --
------------          --
----######--          --
----######--          --
----######--          --
------------          --
------------          --
------------------------
------------------------""")
    assert m.find_starting_corner() == (12, 2)
    assert m.get_bottom_bounds(12, 2) == [9, 16]


# bad_shape_for - bsf

def test_bsf_rejects_when_too_small():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))

    assert m.too_small(5, 5)
    assert m.too_small(5, 6)
    assert m.too_small(6, 5)
    assert not m.too_small(6, 6)

    assert m.bad_shape_for((5, 5), 1, 1)
    assert m.bad_shape_for((5, 6), 1, 1)
    assert m.bad_shape_for((6, 5), 1, 1)
    assert not m.bad_shape_for((6, 6), 1, 1)

def test_bsf_rejects_when_too_skinny():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=1, aspect_min=0.3)
    assert m.too_skinny(14, 3)
    assert m.bad_shape_for((14, 3), 1, 1)

def test_bsf_rejects_when_not_enough_room():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=1)
    m.load("""\
----------------
-              -
-              -
-              -
-              -
-  ---         -
-  -#-         -
----------------""")

    assert m.enough_room(3, 4, 1, 1)
    assert not m.bad_shape_for((3, 4), 1, 1)
    assert not m.enough_room(3, 5, 1, 1)
    assert m.bad_shape_for((3, 5), 1, 1)

    assert m.enough_room(14, 3, 1, 1)
    assert not m.bad_shape_for((14, 3), 1, 1)
    assert not m.enough_room(15, 3, 1, 1)
    assert m.bad_shape_for((15, 3), 1, 1)

def test_bsf_doesnt_ignore_intervening_shape_when_looking_for_enough_room():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=1)
    m.load("""\
----------------
-              -
------         -
--###-         -
------         -
-              -
-   #          -
----------------""")

    assert not m.enough_room(3, 4, 1, 1)
    assert m.bad_shape_for((3, 4), 1, 1)


# get_snapped_shapes - gss

def test_gss_gets_snapped_shapes():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    assert m.get_snapped_shapes(1, 1, 84) == [(14, 6)]

def test_gss_gets_snapped_shape_for_half_area():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=1)
    assert m.get_snapped_shapes(1, 1, 42) == [(14, 3), (7, 6)]

def test_gss_respects_building_min():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=1)
    assert m.get_snapped_shapes(1, 1, 42) == [(14, 3), (7, 6)]
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=2)
    assert m.get_snapped_shapes(1, 1, 42) == [(7, 6)]

def test_gss_respects_building_min_again():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=10, building_min=1)
    m.add(9, 'a', shape_choice=1)
    assert m.get_snapped_shapes(12, 1, 18) == [(3, 6)]

def test_gss_gets_snapped_shape_for_half_area_on_larger_canvas():
    m = genmap.MagnitudeMap(canvas_size=(16, 12), building_min=1)
    assert m.get_snapped_shapes(1, 1, 42) == [(14, 3), (4, 10)]

def test_gss_exhibits_pinch_prevention():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=10, building_min=1)
    assert m.get_snapped_shapes(1, 1, 75) == [(14, 3), (11, 6)]
    """

    We want this:       Instead of this:

    ----------------    ----------------
    ----------------    ----------------
    --############--    --############--
    ----------------    --############--
    -              -    --############--
    -              -    ----------------
    -              -    -              -
    ----------------    ----------------

    ----------------    ----------------
    ------------   -    -------------  -
    --#########-   -    --##########-  -
    --#########-   -    --##########-  -
    --#########-   -    --##########-  -
    --#########-   -    --##########-  -
    ------------   -    -------------  -
    ----------------    ----------------

    """

def test_gss_will_two_snap_to_a_soft_and_hard_bound():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), building_min=1)
    m.load("""\
----------------
-------        -
--####-        -
--####-        -
-------        -
-              -
-              -
----------------
""")
    assert m.find_starting_corner() == (7, 1)
    assert m.get_bottom_bounds(7, 1) == [5, 7]
    assert m.get_snapped_shapes(7, 1, 32) == [(8, 4)]


# get_unsnapped_shapes - gus

def test_gus_gets_unsnapped_shapes():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    assert m.get_unsnapped_shapes(1, 1, 36) == [(6, 6)]

def test_gus_gets_multiple_unsnapped_shapes():
    m = genmap.MagnitudeMap(canvas_size=(16, 12))  # NB: bigger canvas
    assert m.get_unsnapped_shapes(1, 1, 48) == [(6, 8), (7, 6), (8, 6)]


# draw_half_alleys_around_shape - dhaas

def test_dhaas_draws_half_alleys_around_shape():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    m.draw_half_alleys_around_shape((5, 1), 2, 2)
    assert str(m) == """\
----------------
--------       -
--     -       -
--------       -
-              -
-              -
-              -
----------------"""


# draw_shape_at - dsa

def test_dsa_draws_shape_at():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    m.draw_shape_at((14, 6), 1, 1)
    assert str(m) == """\
----------------
----------------
--############--
--############--
--############--
--############--
----------------
----------------"""

def test_dsa_draws_shape_that_doesnt_use_whole_canvas():
    m = genmap.MagnitudeMap(canvas_size=(16, 8))
    m.draw_shape_at((8, 6), 7, 1)
    assert str(m) == """\
----------------
-      ---------
-      -######--
-      -######--
-      -######--
-      -######--
-      ---------
----------------"""


# add

def test_add_adds():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=10)
    m.add(10, 'a')
    assert str(m) == """\
----------------
----------------
--############--
--############--
--############--
--############--
----------------
----------------"""

def test_add_adds_a_half_magnitude():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=10, building_min=1)
    m.add(5, 'a', shape_choice=0)
    assert str(m) == """\
----------------
----------------
--############--
----------------
-              -
-              -
-              -
----------------"""

def test_add_adds_the_other_shape_for_a_half_magnitude():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=10, building_min=1)
    m.add(5, 'a', shape_choice=1)
    assert str(m) == """\
----------------
--------       -
--#####-       -
--#####-       -
--#####-       -
--#####-       -
--------       -
----------------"""

def test_add_adds_a_second_magnitude():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=10, building_min=1)
    m.add(5, 'a', shape_choice=1)
    m.add(5, 'b')
    assert str(m) == """\
----------------
----------------
--#####--#####--
--#####--#####--
--#####--#####--
--#####--#####--
----------------
----------------"""

def test_add_adds_magnitudes_with_different_ratios():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=7, building_min=1)
    m.add(4, 'a', shape_choice=1)
    m.add(3, 'b')
    assert str(m) == """\
----------------
----------------
--######--####--
--######--####--
--######--####--
--######--####--
----------------
----------------"""

def test_add_exhibits_pinch_prevention():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=10, building_min=1)
    m.add(9, 'a', shape_choice=0)
    m.add(1, 'b')
    assert str(m) == """\
----------------
----------------
--############--
----------------
----------------
--############--
----------------
----------------"""

def test_add_exhibits_pinch_prevention_the_other_way():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=10, building_min=1)
    m.add(9, 'a', shape_choice=1)
    m.add(1, 'b')
    assert str(m) == """\
----------------
----------------
--#########--#--
--#########--#--
--#########--#--
--#########--#--
----------------
----------------"""

def test_add_will_two_snap_to_a_soft_and_hard_bound():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=15, building_min=1)
    m.load("""\
----------------
-------        -
--####-        -
--####-        -
-------        -
-              -
-              -
----------------""")
    m.add(8, 'a')
    assert str(m) == """\
----------------
----------------
--####--######--
--####--######--
----------------
-              -
-              -
----------------"""


# assign_ids - ai

def test_ai_assigns_ids():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=10, building_min=1)
    m.add(5, 'a', shape_choice=1)
    m.add(5, 'b')
    assert str(m) == """\
----------------
----------------
--#####--#####--
--#####--#####--
--#####--#####--
--#####--#####--
----------------
----------------"""
    assert m.assignments == {}
    m.assign_ids({'art': ['deadbeef', 'beeffeed']})
    assert m.assignments == {'a': 'deadbeef', 'b': 'beeffeed'}

def test_ai_handles_two_pathways():
    m = genmap.MagnitudeMap(canvas_size=(16, 8), sum_of_magnitudes=84, building_min=1)
    m.add(24, 'a')
    m.add(30, 'b', shape_choice=0)
    m.add(30, 'c')
    assert str(m) == """\
----------------
----------------
--##--########--
--##------------
--##------------
--##--########--
----------------
----------------"""
    assert m.assignments == {}
    m.assign_ids({'art': ['dead', 'beef'], 'science': ['feed']})
    possible_assignments = [
        {'a': 'dead', 'b': 'beef', 'c': 'feed'},
        {'a': 'dead', 'b': 'feed', 'c': 'beef'},
        {'a': 'beef', 'b': 'feed', 'c': 'dead'},
        {'a': 'beef', 'b': 'dead', 'c': 'feed'},
        {'a': 'feed', 'b': 'dead', 'c': 'beef'},
        {'a': 'feed', 'b': 'beef', 'c': 'dead'},
    ]
    assert m.assignments in possible_assignments
