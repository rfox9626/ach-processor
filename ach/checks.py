from ach.nacha.fields import check_digit
from .models import Account

def check_routing(routing: str) -> str | None:
    if len(routing) != 9 or not routing.isdigit():
        return "R28"

    check = check_digit(routing[:8])

    if check == routing[8]:
        return None

    return check


def check_account(account: Account | None) -> str | None:
    if account is None:
        return "R03"

    if account.status == Account.AccountStatus.CLOSED:
        return "R02"

    if account.status == Account.AccountStatus.FROZEN:
        return "R16"

    return None


def check_limit(account: Account, used_cents: int, amount_cents: int) -> str | None:
    total_cents = used_cents + amount_cents

    if total_cents > account.daily_limit_cents:
        # Bank policy: R01 used for daily-limit breaches (NACHA has no 
        # limit-specific code)
        return "R01"

    return None
