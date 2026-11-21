from django.core.management.base import BaseCommand
from django.db import transaction
from ach.fakes.pool import build_pool
from ach.models import Account, Customer

class Command(BaseCommand):
    help = "Load the generator's pool into Customer and Account"

    def handle(self, *args, **options):
        _, receivers, _ = build_pool()
        created = updated = 0
        with transaction.atomic():
            for r in receivers:
                account = (
                    Account.objects
                    .filter(routing=r["routing"], account_number=r["account_number"])
                    .select_related("customer")
                    .first()
                )

                if account:                                        # already loaded: bring it up to date
                    account.kind = r["kind"].upper()
                    account.status = r["status"].upper()
                    account.save(update_fields=["kind", "status"])
                    account.customer.name = r["name"]
                    account.customer.save(update_fields=["name"])
                    updated += 1
                else:                                              # new: the customer first, then the account
                    customer = Customer.objects.create(
                        name=r["name"],
                        kind=Customer.CustKind.INDIVIDUAL,
                    )

                    Account.objects.create(
                        customer=customer,
                        routing=r["routing"],
                        account_number=r["account_number"],
                        kind=r["kind"].upper(),
                        status=r["status"].upper(),
                    )
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"{created} created, {updated} updated"))
