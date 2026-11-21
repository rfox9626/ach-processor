import pytest
from django.core.management import call_command

from ach.fakes.pool import build_pool
from ach.models import Account

@pytest.mark.django_db
def test_seeded_accounts_match_pool():
    call_command("seed_accounts")
    _, receivers, _ = build_pool()
    for r in receivers:
        assert Account.objects.filter(routing=r["routing"],
                                      account_number=r["account_number"]).exists()
    assert Account.objects.filter(status=Account.AccountStatus.CLOSED).count() == 5
