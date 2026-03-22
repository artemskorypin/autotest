import requests

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = "17678"

INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1

SESSION = requests.Session()
SESSION.trust_env = False

def _normalize_state(s: str) -> str: 
    # рус К О eng K O
    # заменяем кириллическую 'К' на латинскую 'K'
    return s.replace("К", "K").replace("О", "O")

def assert_ok_result(resp, expected: int):
    assert resp.status_code == 200, f'status_code = {resp.status_code}'
    data = resp.json()
    # assert data == {"statusCode": 0, "result": expected}, f"incorrect data:\n{data}"
    assert isinstance(data, dict) 
    assert data.get("statusCode") == 0, f'statusCode = {data.get("statusCode")}'
    assert "result" in data
    assert isinstance(data["result"], int)
    assert data["result"] == expected, f'data["result"] = {data["result"]}\nexpected = {expected}'


def assert_error(resp, expected_code: int):
    assert resp.status_code == 200, f'status_code = {resp.status_code}'
    data = resp.json()
    assert isinstance(data, dict)
    assert data.get("statusCode") == expected_code, f'statusCode = {data.get("statusCode")}\nexpected_code = {expected_code}\nData = {data}'
    assert "statusMessage" in data
    assert isinstance(data["statusMessage"], str)
    assert data["statusMessage"]  # не пусто