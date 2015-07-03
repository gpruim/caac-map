import genmap
from pytest import raises


def test_map_can_draw_an_empty_canvas():
    m = genmap.MagnitudeMap(canvas_size=(12, 4), sum_of_magnitudes=0)
    assert unicode(m) == """\
----------------
----------------
--            --
--            --
--            --
--            --
----------------
----------------"""


def test_map_can_draw_an_empty_canvas_with_different_size():
    m = genmap.MagnitudeMap(canvas_size=(32, 8), alley_width=4)
    assert unicode(m) == """\
----------------------------------------
----------------------------------------
----------------------------------------
----------------------------------------
----                                ----
----                                ----
----                                ----
----                                ----
----                                ----
----                                ----
----                                ----
----                                ----
----------------------------------------
----------------------------------------
----------------------------------------
----------------------------------------"""


# find_first_empty_cell - ffec

def test_ffec_finds_first_empty_cell():
    m = genmap.MagnitudeMap(canvas_size=(12, 4))
    assert m.find_first_empty_cell() == (2, 2)


# determine_target_area - dta

def test_dta_determines_target_area():
    m = genmap.MagnitudeMap(canvas_size=(12, 4), sum_of_magnitudes=10)
    assert m.determine_target_area(10) == 48

def test_dta_prorates_based_on_sum_of_magnitudes():
    m = genmap.MagnitudeMap(canvas_size=(12, 4), sum_of_magnitudes=20)
    assert m.determine_target_area(10) == 24

def test_dta_varies_with_canvas_size():
    m = genmap.MagnitudeMap(canvas_size=(12, 12), sum_of_magnitudes=20)
    assert m.determine_target_area(10) == 72

def test_dta_enforces_lower_bound():
    m = genmap.MagnitudeMap(canvas_size=(10, 10), sum_of_magnitudes=20)
    with raises(genmap.TargetAreaTooSmall):
        m.determine_target_area(3)


# get_right_bounds - grb

def test_grb_gets_right_bounds():
    m = genmap.MagnitudeMap(canvas_size=(12, 4))
    assert m.get_right_bounds(2, 2) == [14]


# get_bottom_bounds - gbb

def test_gbb_gets_bottom_bounds():
    m = genmap.MagnitudeMap(canvas_size=(12, 4))
    assert m.get_bottom_bounds(2, 2) == [6]


# get_snapped_shapes - gss

def test_gss_gets_snapped_shapes():
    m = genmap.MagnitudeMap(canvas_size=(12, 4))
    assert m.get_snapped_shapes(2, 2, 48) == [(12, 4)]

def test_gss_gets_snapped_shape_for_half_area():
    m = genmap.MagnitudeMap(canvas_size=(12, 4), block_min=1)
    assert m.get_snapped_shapes(2, 2, 24) == [(12, 2), (6, 4)]

def test_gss_gets_snapped_shape_respects_block_min():
    m = genmap.MagnitudeMap(canvas_size=(12, 4), block_min=2)
    assert m.get_snapped_shapes(2, 2, 24) == [(12, 2), (6, 4)]
    m = genmap.MagnitudeMap(canvas_size=(12, 4), block_min=3)
    assert m.get_snapped_shapes(2, 2, 24) == [(6, 4)]

def test_gss_gets_snapped_shape_for_half_area_on_larger_canvas():
    m = genmap.MagnitudeMap(canvas_size=(12, 8), block_min=1)
    assert m.get_snapped_shapes(2, 2, 24) == [(12, 2), (3, 8)]


# draw_alleys_around_shape - daas

def test_daas_draws_alleys_around_shape():
    m = genmap.MagnitudeMap(canvas_size=(12, 4))
    m.draw_alleys_around_shape((5, 1), 2, 2)
    assert unicode(m) == """\
----------------
----------------
--     --     --
---------     --
---------     --
--            --
----------------
----------------"""


# draw_shape_at - dsa

def test_dsa_draws_shape_at():
    m = genmap.MagnitudeMap(canvas_size=(12, 4))
    m.draw_shape_at((12, 4), 2, 2)
    assert unicode(m) == """\
----------------
----------------
--############--
--############--
--############--
--############--
----------------
----------------"""

def test_dsa_draws_shape_that_doesnt_use_whole_canvas():
    m = genmap.MagnitudeMap(canvas_size=(12, 4))
    m.draw_shape_at((6, 4), 8, 2)
    assert unicode(m) == """\
----------------
----------------
--    --######--
--    --######--
--    --######--
--    --######--
----------------
----------------"""


# add

def test_add_adds():
    m = genmap.MagnitudeMap(canvas_size=(12, 4), sum_of_magnitudes=10)
    m.add(10)
    assert unicode(m) == """\
----------------
----------------
--############--
--############--
--############--
--############--
----------------
----------------"""

def test_add_adds_a_half_magnitude():
    m = genmap.MagnitudeMap(canvas_size=(12, 4), sum_of_magnitudes=10, block_min=2)
    m.add(5, shape_choice=0)
    assert unicode(m) == """\
----------------
----------------
--############--
--############--
----------------
----------------
----------------
----------------"""

def test_add_adds_the_other_half_magnitude():
    m = genmap.MagnitudeMap(canvas_size=(12, 4), sum_of_magnitudes=10, block_min=2)
    m.add(5, shape_choice=1)
    assert unicode(m) == """\
----------------
----------------
--######--    --
--######--    --
--######--    --
--######--    --
----------------
----------------"""

def test_add_adds_a_second_magnitude():
    m = genmap.MagnitudeMap(canvas_size=(12, 4), sum_of_magnitudes=12, block_min=2)
    m.add(6, shape_choice=1)
    m.add(4)
    assert unicode(m) == """\
----------------
----------------
--######--####--
--######--####--
--######--####--
--######--####--
----------------
----------------"""
