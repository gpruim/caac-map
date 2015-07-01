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
