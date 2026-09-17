"""JSON schemas for the 5 ReqRes APIs used by the framework."""
from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

# GET /api/users?delay=N
USER = {
    "type": "object",
    "required": ["id", "email", "first_name", "last_name", "avatar"],
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string", "pattern": r"^[^@\s]+@[^@\s]+$"},
        "first_name": {"type": "string", "minLength": 1},
        "last_name": {"type": "string", "minLength": 1},
        "avatar": {"type": "string", "pattern": r"^https?://"},
    },
}
USER_LIST = {
    "type": "object",
    "required": ["page", "per_page", "total", "total_pages", "data"],
    "properties": {
        "page": {"type": "integer", "minimum": 1},
        "per_page": {"type": "integer", "minimum": 1},
        "total": {"type": "integer", "minimum": 0},
        "total_pages": {"type": "integer", "minimum": 0},
        "data": {"type": "array", "items": USER},
    },
}

# POST /api/users
CREATED_USER = {
    "type": "object",
    "required": ["name", "job", "id", "createdAt"],
    "properties": {
        "name": {"type": "string"},
        "job": {"type": "string"},
        "id": {"type": ["string", "integer"]},
        "createdAt": {"type": "string"},
    },
}

# PUT / PATCH /api/users/{id}
UPDATED_USER = {
    "type": "object",
    "required": ["updatedAt"],
    "properties": {"updatedAt": {"type": "string"}},
}


def assert_schema(instance: Any, schema: dict, name: str) -> None:
    """Validate `instance` and report every violation in one readable message."""
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda e: list(e.path))
    if errors:
        details = "\n".join(
            f"  - at '{'/'.join(map(str, e.path)) or '<root>'}': {e.message}" for e in errors[:10]
        )
        raise AssertionError(f"Response does not match the '{name}' schema:\n{details}")
