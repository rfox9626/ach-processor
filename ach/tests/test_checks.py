import pytest

from ach.checks import check_account, check_limit, check_routing
from ach.models import Account


@pytest.mark.parametrize(
    "routing, expected",
    [
        ("042000013", None),     # valid
        ("042000014", "R28"),    # bad check digit
        ("04200001", "R28"),     # 8 digits
        ("04200001X", "R28"),    # not numeric
    ],
)


def test_check_routing(routing, expected):
    assert check_routing(routing) == expected


@pytest.mark.parametrize(
    "status, expected",
    [
        (Account.AccountStatus.OPEN, None),
        (Account.AccountStatus.CLOSED, "R02"),
        (Account.AccountStatus.FROZEN, "R16"),
    ],
)


def test_check_account(status, expected):
    account = Account(status=status)      
    assert check_account(account) == expected


def test_check_account_missing():
    assert check_account(None) == "R03"


@pytest.mark.parametrize(
    "used, amount, expected",
    [
        (0, 10_000, None),
        (40_000, 10_000, None),      # exactly at the limit
        (40_000, 10_001, "R01"),     # one cent over
        (0, 60_000, "R01"),          # a single entry over the limit
    ],
)


def test_check_limit(used, amount, expected):
    account = Account(daily_limit_cents=50_000)
    assert check_limit(account, used, amount) == expected
