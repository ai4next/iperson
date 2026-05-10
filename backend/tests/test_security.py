"""Tests for core security (JWT, password hashing, RBAC)."""

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    role_ge,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pwd = "my-secure-password-123"
        hashed = hash_password(pwd)
        assert hashed != pwd
        assert verify_password(pwd, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False


class TestJWT:
    def test_create_and_decode_access_token(self):
        token = create_access_token("user1", "tenant1", "editor")
        payload = decode_token(token)
        assert payload["sub"] == "user1"
        assert payload["tenant_id"] == "tenant1"
        assert payload["role"] == "editor"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_and_decode_refresh_token(self):
        token = create_refresh_token("user1", "tenant1")
        payload = decode_token(token)
        assert payload["sub"] == "user1"
        assert payload["tenant_id"] == "tenant1"
        assert payload["type"] == "refresh"


class TestRBAC:
    def test_role_hierarchy(self):
        assert role_ge("owner", "admin") is True  # owner ≥ viewer
        assert role_ge("editor", "viewer") is True
        assert role_ge("admin", "viewer") is True
        assert role_ge("viewer", "editor") is False  # viewer < editor
        assert role_ge("owner", "owner") is True