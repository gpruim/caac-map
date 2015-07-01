import genmap
from pytest import raises


def test_map_can_draw_an_empty_canvas():
    m = genmap.MagnitudeMap(canvas_size=(32, 8), sum_of_magnitudes=0)
    assert unicode(m) == """\
------------------------------------
------------------------------------
--                                --
--                                --
--                                --
--                                --
--                                --
--                                --
--                                --
--                                --
------------------------------------
------------------------------------"""


def test_map_can_draw_an_empty_canvas_with_different_alleys():
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
    m = genmap.MagnitudeMap(canvas_size=(12, 4), sum_of_magnitudes=10)
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
