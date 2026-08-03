import pytest

from app.modules.auth.security import (
    InvalidTokenError,
    create_access_token,
    create_user_access_token,
    decode_access_token,
    decode_user_access_token,
)


def test_user_and_admin_tokens_are_isolated():
    user_token, _ = create_user_access_token(subject="user-id")
    admin_token, _ = create_access_token(subject="admin-id", role="super_admin")

    assert decode_user_access_token(user_token)["sub"] == "user-id"
    assert decode_access_token(admin_token)["sub"] == "admin-id"
    with pytest.raises(InvalidTokenError):
        decode_access_token(user_token)
    with pytest.raises(InvalidTokenError):
        decode_user_access_token(admin_token)
