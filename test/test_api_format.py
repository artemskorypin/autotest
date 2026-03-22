import pytest
from tests.utils import assert_error, INT32_MIN, INT32_MAX, _normalize_state, SESSION

# формальная проверка, что приложение поднялось, возможно лишняя, тк конфиг проверяет запуск
def test_state_format(app):
    r = SESSION.get(f"{app.base_url}/api/state", timeout=2.0)
    assert r.status_code == 200
    data = r.json()
    # assert data == {"statusCode": 0, "state": "OK"}, f"incorrect data:\n{data}"
    assert isinstance(data, dict) 
    assert data.get("statusCode") == 0, f'statusCode = {data.get("statusCode")}'
    assert "state" in data
    assert _normalize_state(data["state"]) == "OK", f'state = {data.get("state")}'
    

@pytest.mark.parametrize("endpoint", ["addition", "multiplication", "division", "remainder"])
def test_post_requires_json_key_x(app, endpoint):
    # нет ключа y => код 2 (не хватает ключей)
    r = SESSION.post(f"{app.base_url}/api/{endpoint}", json={"x": 1}, timeout=2.0)
    assert_error(r, 2)
    
    
@pytest.mark.parametrize("endpoint", ["addition", "multiplication", "division", "remainder"])
def test_post_requires_json_key_y(app, endpoint):
    # нет ключа x => код 2
    r2 = SESSION.post(f"{app.base_url}/api/{endpoint}", json={"y": 1}, timeout=2.0)
    assert_error(r2, 2)


@pytest.mark.parametrize("bad_value", [True, False, [], {}, None, "1", 2.5])
@pytest.mark.parametrize("endpoint", ["addition", "multiplication", "division", "remainder"])
def test_post_rejects_non_integer_types_extended_x(app, endpoint, bad_value):
    # x не int => код 3
    r1 = SESSION.post(f"{app.base_url}/api/{endpoint}", json={"x": bad_value, "y": 2}, timeout=2.0)
    assert_error(r1, 3)
    
    
@pytest.mark.parametrize("bad_value", [True, False, [], {}, None, "1", 2.5])
@pytest.mark.parametrize("endpoint", ["addition", "multiplication", "division", "remainder"])
def test_post_rejects_non_integer_types_extended_y(app, endpoint, bad_value):
    # x не int => код 3
    r2 = SESSION.post(f"{app.base_url}/api/{endpoint}", json={"x": 2, "y": bad_value}, timeout=2.0)
    assert_error(r2, 3)


@pytest.mark.parametrize("endpoint", ["addition", "multiplication", "division", "remainder"])
@pytest.mark.parametrize('value', [INT32_MAX + 1, INT32_MIN - 1])
def test_post_rejects_out_of_int32_x(app, endpoint, value):
    # выход за int32 => код 4
    r = SESSION.post(f"{app.base_url}/api/{endpoint}", json={"x": value, "y": 0}, timeout=2.0)
    assert_error(r, 4)
    

@pytest.mark.parametrize("endpoint", ["addition", "multiplication", "division", "remainder"])
@pytest.mark.parametrize('value', [INT32_MAX + 1, INT32_MIN - 1])
def test_post_rejects_out_of_int32_y(app, endpoint, value):
    # выход за int32 => код 4        
    r2 = SESSION.post(f"{app.base_url}/api/{endpoint}", json={"x": 0, "y": value}, timeout=2.0)
    assert_error(r2, 4)
    
    
@pytest.mark.parametrize("endpoint", ["addition", "multiplication", "division", "remainder"])
def test_post_rejects_invalid_json_body(app, endpoint):
    # Неправильный формат тела запроса => код 5
    headers = {"Content-Type": "application/json"}
    r = SESSION.post(
        f"{app.base_url}/api/{endpoint}",
        data="{not a json}",
        headers=headers, 
        timeout=2.0,
    )
    assert_error(r, 5)