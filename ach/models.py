from django.db import models


class Customer(models.Model):
    def __str__(self):
        return self.name

    class CustKind(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        BUSINESS = "BUSINESS", "Business"

    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=CustKind.choices)


class Account(models.Model):
    def __str__(self):
        return f"{self.account_number} ({self.kind}, {self.status})"

    class AccountKind(models.TextChoices):
        CHECKING = "CHECKING", "Checking"
        SAVINGS = "SAVINGS", "Savings"

    class AccountStatus(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"
        FROZEN = "FROZEN", "Frozen"

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="accounts")
    routing = models.CharField(max_length=9)
    account_number = models.CharField(max_length=17)
    kind = models.CharField(max_length=10, choices=AccountKind.choices)

    status = models.CharField(
        max_length=10, choices=AccountStatus.choices, default=AccountStatus.OPEN
    )

    balance_cents = models.BigIntegerField(default=0)
    daily_limit_cents = models.BigIntegerField(default=1_000_000)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["routing", "account_number"], name="account_unique_routing_number"
            ),
        ]


class Entry(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VALID = "VALID", "Valid"
        INVALID = "INVALID", "Invalid"
        RECEIVED = "RECEIVED", "Received"

    ach_file = models.ForeignKey("AchFile", on_delete=models.CASCADE, related_name="entries")

    batch = models.ForeignKey("Batch", on_delete=models.CASCADE, related_name="entries")
    transaction_code = models.CharField(max_length=2)
    routing_number = models.CharField(max_length=9)
    account_number = models.CharField(max_length=17)
    amount_cents = models.BigIntegerField()
    individual_id = models.CharField(max_length=15, blank=True)
    individual_name = models.CharField(max_length=22)
    trace_number = models.CharField(max_length=15)
    addenda_type = models.CharField(max_length=2, blank=True)
    addenda_info = models.CharField(max_length=80, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reject_reason = models.TextField(blank=True, default="")
    return_code = models.CharField(max_length=3, blank=True)

    class Meta:
        verbose_name_plural = "entries"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_cents__gte=0),
                name="entry_amount_non_negative",
            ),
            models.UniqueConstraint(
                fields=["ach_file", "trace_number"],
                name="trace_number_unique_per_file",
            ),
        ]

    def __str__(self):
        return f"{self.trace_number} - {self.amount_cents}"


class Batch(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VALID = "VALID", "Valid"
        INVALID = "INVALID", "Invalid"
        RECEIVED = "RECEIVED", "Received"

    ach_file = models.ForeignKey("AchFile", on_delete=models.CASCADE, related_name="batches")

    batch_number = models.IntegerField()
    service_class = models.CharField(max_length=3)
    company_name = models.CharField(max_length=16)
    company_id = models.CharField(max_length=10)
    sec_code = models.CharField(max_length=3)
    entry_description = models.CharField(max_length=10, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    originating_dfi = models.CharField(max_length=8, blank=True)
    entry_count = models.IntegerField(default=0)
    total_debit_cents = models.BigIntegerField(default=0)
    total_credit_cents = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["ach_file", "batch_number"], name="batch_number_unique_per_file"
            ),
        ]
        verbose_name_plural = "batches"

    def __str__(self):
        return f"{self.company_name} - Batch {self.batch_number}"


class AchFile(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VALID = "VALID", "Valid"
        INVALID = "INVALID", "Invalid"
        RECEIVED = "RECEIVED", "Received"
        PARSED = "PARSED", "Parsed"
        CHECKED = "CHECKED", "Checked"

    file_name = models.CharField(max_length=255, blank=True)
    sha256 = models.CharField(max_length=64, unique=True)
    immediate_destination = models.CharField(max_length=10, blank=True)
    immediate_origin = models.CharField(max_length=10, blank=True)
    destination_name = models.CharField(max_length=23, blank=True)
    origin_name = models.CharField(max_length=23, blank=True)
    creation_date = models.DateField(null=True, blank=True)
    creation_time = models.CharField(max_length=4, blank=True)
    id_modifier = models.CharField(max_length=1, blank=True)
    batch_count = models.IntegerField(default=0)
    entry_count = models.IntegerField(default=0)
    total_debit_cents = models.BigIntegerField(default=0)
    total_credit_cents = models.BigIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    reject_reason = models.TextField(blank=True, default="")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_name}"


class DailyUsage(models.Model):
    account = models.ForeignKey("Account", on_delete=models.PROTECT)
    date = models.DateField()
    used_cents = models.BigIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["account", "date"], name="account_number_unique_per_day"
            ),
        ]

    def __str__(self):
        return f"{self.account_id} - {self.date} - {self.used_cents}"
