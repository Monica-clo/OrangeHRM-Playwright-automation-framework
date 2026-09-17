"""ReqRes user API validation - response body + status code for 5 APIs.

1. POST   https://reqres.in/api/users           {"name":"morpheus","job":"leader"}        -> 201
2. PUT    https://reqres.in/api/users/2         {"name":"morpheus","job":"zion resident"} -> 200
3. PATCH  https://reqres.in/api/users/2         {"job":"zion resident"}                   -> 200
4. DELETE https://reqres.in/api/users/2                                                   -> 204
5. GET    https://reqres.in/api/users?delay=2                                             -> 200

Inputs and expected values: test_data/api/reqres_test_data.json -> "user_apis".
"""
from datetime import datetime, timedelta, timezone

import pytest

from api.base_client import ApiResponse
from api.reqres_client import ReqResClient
from api.schemas import CREATED_USER, UPDATED_USER, USER_LIST, assert_schema
from utils.data_reader import load_reqres_data
from utils.reporting import step

DATA = load_reqres_data()["user_apis"]

# Run all ReqRes calls on ONE parallel worker so the client-side throttle protects the rate limit
pytestmark = pytest.mark.xdist_group("reqres_api")


# ---------------------------------------------------------------------------- helpers
def assert_status_code(response: ApiResponse, expected: int) -> None:
    assert response.status == expected, (
        f"{response.method} {response.url}: expected status code {expected}, "
        f"but got {response.status}. Response body: {response.text[:300]}"
    )


def assert_fields_echoed(body: dict, payload: dict) -> None:
    """Every field sent in the request must come back with the same value."""
    mismatches = [
        f"  - {field}: sent {value!r}, got {body.get(field)!r}"
        for field, value in payload.items()
        if body.get(field) != value
    ]
    assert not mismatches, "Response does not echo the request payload:\n" + "\n".join(mismatches)


def assert_recent_timestamp(body: dict, field: str) -> None:
    """The timestamp must be a valid ISO-8601 date close to the current time."""
    value = body.get(field)
    assert value, f"'{field}' is missing in the response: {body}"
    try:
        timestamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        raise AssertionError(f"'{field}' is not a valid ISO-8601 timestamp: {value!r}") from None
    age = abs(datetime.now(timezone.utc) - timestamp)
    assert age < timedelta(days=1), f"'{field}' should be close to now, got {value!r}"


# ---------------------------------------------------------------------------- 1. POST
@pytest.mark.smoke
def test_create_user_post(reqres: ReqResClient) -> None:
    case = DATA["create_user"]
    payload = case["payload"]

    with step(f"POST /api/users with {payload}"):
        response = reqres.create_user(payload["name"], payload["job"])

    with step(f"Validate status code is {case['expected_status']}"):
        assert_status_code(response, case["expected_status"])

    with step("Validate response body"):
        body = response.json()
        assert_schema(body, CREATED_USER, "created user")
        assert_fields_echoed(body, payload)
        assert str(body["id"]).strip(), f"A new 'id' should be generated, got {body['id']!r}"
        assert_recent_timestamp(body, "createdAt")


# ---------------------------------------------------------------------------- 2. PUT
def test_update_user_put(reqres: ReqResClient) -> None:
    case = DATA["update_user_put"]
    payload = case["payload"]

    with step(f"PUT /api/users/{case['user_id']} with {payload}"):
        response = reqres.update_user(case["user_id"], payload["name"], payload["job"])

    with step(f"Validate status code is {case['expected_status']}"):
        assert_status_code(response, case["expected_status"])

    with step("Validate response body"):
        body = response.json()
        assert_schema(body, UPDATED_USER, "updated user")
        assert_fields_echoed(body, payload)
        assert_recent_timestamp(body, "updatedAt")


# ---------------------------------------------------------------------------- 3. PATCH
def test_update_user_patch(reqres: ReqResClient) -> None:
    case = DATA["update_user_patch"]
    payload = case["payload"]

    with step(f"PATCH /api/users/{case['user_id']} with {payload}"):
        response = reqres.patch_user(case["user_id"], payload)

    with step(f"Validate status code is {case['expected_status']}"):
        assert_status_code(response, case["expected_status"])

    with step("Validate response body"):
        body = response.json()
        assert_schema(body, UPDATED_USER, "patched user")
        assert_fields_echoed(body, payload)
        assert_recent_timestamp(body, "updatedAt")


# ---------------------------------------------------------------------------- 4. DELETE
def test_delete_user(reqres: ReqResClient) -> None:
    case = DATA["delete_user"]

    with step(f"DELETE /api/users/{case['user_id']}"):
        response = reqres.delete_user(case["user_id"])

    with step(f"Validate status code is {case['expected_status']}"):
        assert_status_code(response, case["expected_status"])

    with step("Validate response body is empty"):
        assert response.text.strip() == "", f"DELETE should return no body, got {response.text!r}"


# ---------------------------------------------------------------------------- 5. GET (delayed)
def test_get_users_with_delay(reqres: ReqResClient) -> None:
    case = DATA["delayed_get_users"]
    expected = case["expected"]

    with step(f"GET /api/users?delay={case['delay_seconds']}"):
        response = reqres.list_users_delayed(case["delay_seconds"])

    with step(f"Validate status code is {case['expected_status']}"):
        assert_status_code(response, case["expected_status"])

    with step(f"Validate the response was delayed by about {case['delay_seconds']}s"):
        minimum_ms = case["delay_seconds"] * 1000 * 0.9
        maximum_ms = case["max_response_seconds"] * 1000
        assert response.elapsed_ms >= minimum_ms, (
            f"Response should take at least {case['delay_seconds']}s, took {response.elapsed_ms:.0f} ms"
        )
        assert response.elapsed_ms <= maximum_ms, (
            f"Response took too long: {response.elapsed_ms:.0f} ms (limit {case['max_response_seconds']}s)"
        )

    with step("Validate response body"):
        body = response.json()
        assert_schema(body, USER_LIST, "user list")
        for field, value in expected.items():
            assert body[field] == value, f"'{field}' should be {value}, got {body[field]}"
        assert len(body["data"]) == expected["per_page"], (
            f"Expected {expected['per_page']} users, got {len(body['data'])}"
        )
        ids = [user["id"] for user in body["data"]]
        assert ids == list(range(1, expected["per_page"] + 1)), f"Page 1 should list ids 1-6, got {ids}"
