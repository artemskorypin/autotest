import pytest
from tests.utils import assert_ok_result, assert_error, SESSION, INT32_MAX, INT32_MIN

def post(app, endpoint: str, x: int, y: int):
    return SESSION.post(
        f"{app.base_url}/api/{endpoint}",
        json={"x": x, "y": y},
        timeout=2.0
    )
    
    
def _addition():
    ls = [
        (1, 2), 
        (0, 0), 
        (-5, 10), 
        (5, -10), 
        (1, 0), 
        (-5, 0),
        (0, 8), 
        (0, -4), 
    ]
    for i, j in ls:
        yield i, j, i + j

@pytest.mark.parametrize(
    "x,y,expected", _addition()
    # [
    #     (1, 2, 3),
    #     (0, 0, 0),
    #     (-5, 10, 5),
    #     (2147483647, 0, 2147483647),
    #     (-2147483648, 0, -2147483648),
    #     (5, -10, -5),
    # ],
)
def test_addition(app, x, y, expected):
    r = post(app, "addition", x, y)
    assert_ok_result(r, expected)


@pytest.mark.parametrize(
    "x,y,expected",
    [
        (2, 3, 6),
        (0, 999, 0),
        (10, 0, 0),
        (-5, 10, -50),
        (5, -10, -50),
        (-5, -5, 25),
        (1, 9, 9),
        (9, 1, 9),
    ],
)
def test_multiplication(app, x, y, expected):
    r = post(app, "multiplication", x, y)
    assert_ok_result(r, expected)


@pytest.mark.parametrize(
    "x,y,expected",
    [
        (7, 2, 3),     # целочисленное деление
        (8, 2, 4),
        (-7, 2, -3),   # ожидаем усечение к нулю
        (7, -2, -3),
        (-9, -2, 4),
        (1, 2, 0),
    ],
)
def test_division(app, x, y, expected):
    r = post(app, "division", x, y)
    assert_ok_result(r, expected)


@pytest.mark.parametrize(
    "x,y,expected",
    [
        (7, 2, 1),
        (8, 2, 0),
        (-7, 2, -1),   # вместе с division может выявлять нюансы реализации
        (7, -2, 1),
        (1, 2, 1),
    ],
)
def test_remainder(app, x, y, expected):
    r = post(app, "remainder", x, y)
    assert_ok_result(r, expected)


@pytest.mark.parametrize("endpoint", ["division", "remainder"])
def test_by_zero_returns_calculation_error(app, endpoint):
    # Ошибка вычисления => код 1
    r = post(app, endpoint, 1, 0)
    assert_error(r, 1)
    
    
@pytest.mark.parametrize("endpoint", ["addition", "multiplication"])
@pytest.mark.parametrize("x,y", [
    (INT32_MAX, 2),
    (INT32_MIN, -2),
])
def test_overflow_is_calc_error(app, endpoint, x, y):
    r = post(app, endpoint, x, y)
    assert_error(r, 1)   # “ошибка вычисления”