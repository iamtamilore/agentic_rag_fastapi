import os
import sys
import pytest
from datetime import timedelta

# Add the project's root directory to the Python path to allow imports from 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_access_token,
)


def test_password_hashing():
    """
    Tests that a password is correctly hashed and can be verified.
    """
    password = "a_strong_password_123"
    hashed_password = hash_password(password)
    assert password != hashed_password
    assert verify_password(password, hashed_password) is True
    assert verify_password("a_wrong_password", hashed_password) is False


def test_access_token_creation_and_verification():
    """
    Tests the full lifecycle of a JWT: creation, encoding, decoding, and verification.
    """
    data_to_encode = {"sub": "iyang.thomas", "role": "clinician"}
    access_token = create_access_token(data=data_to_encode)

    assert isinstance(access_token, str)
    assert len(access_token) > 0

    payload = verify_access_token(access_token)

    assert payload is not None
    assert payload["sub"] == data_to_encode["sub"]
    assert payload["role"] == data_to_encode["role"]


def test_expired_access_token():
    """
    Tests that an expired token correctly fails verification.
    """
    expired_token = create_access_token(
        data={"sub": "testuser"}, expires_delta=timedelta(minutes=-1)
    )
    payload = verify_access_token(expired_token)
    assert payload is None
