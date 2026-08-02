from app.modules.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_argon2_password_hash_does_not_store_plaintext() -> None:
    encoded = hash_password("secure-demo-password")

    assert "secure-demo-password" not in encoded
    assert verify_password("secure-demo-password", encoded)
    assert not verify_password("wrong-password", encoded)


def test_admin_access_token_round_trip() -> None:
    token, expires_in = create_access_token(subject="admin-public-id", role="review_admin")
    payload = decode_access_token(token)

    assert payload["sub"] == "admin-public-id"
    assert payload["role"] == "review_admin"
    assert expires_in > 0
