import pytest
from freezegun import freeze_time

from letsdance.core.crypto import (
    dump_public_key,
    generate_private_key,
    validate_public_key,
)


@pytest.fixture()
def public_key() -> str:
    return dump_public_key(generate_private_key().public_key())


@freeze_time("2022-05-20")
def test_validate_public_key_invalid_ending(public_key):
    """
    The key should be invalid unless it ends with the special pattern.
    """
    key = public_key[:-1] + "a"
    assert not validate_public_key(key)

    # The pattern MUST be at the very end of the key
    key = public_key[:-8] + "83e05209"
    assert not validate_public_key(key)


@freeze_time("2022-05-20")
@pytest.mark.parametrize("date", ["0521", "0422", "0525", "0624"])
def test_validate_public_key_date_invalid(public_key, date):
    """
    The key should be invalid if the date is not within 2 years.
    """
    key = f"{public_key[:-7]}83e{date}"
    assert not validate_public_key(key)


@freeze_time("2022-05-20")
@pytest.mark.parametrize("date", ["0522", "0622", "1223", "0524"])
def test_validate_public_key_valid(public_key, date):
    """
    The key should be valid if the date is within two years.
    """
    key = f"{public_key[:-7]}83e{date}"
    assert validate_public_key(key)
