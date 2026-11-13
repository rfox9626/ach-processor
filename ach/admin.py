from django.contrib import admin

from .models import AchFile, Batch, Entry


class BatchInline(admin.TabularInline):
    model = Batch
    extra = 0
    fields = (
        "company_name",
        "company_id",
        "effective_date",
        "entry_count",
        "total_debit_cents",
        "total_credit_cents",
        "status",
        "batch_number",
    )
    readonly_fields = fields
    show_change_link = True
    can_delete = False


@admin.register(AchFile)
class AchFileAdmin(admin.ModelAdmin):
    list_display = (
        "file_name",
        "uploaded_at",
        "status",
        "origin_name",
        "destination_name",
        "total_debit_cents",
        "total_credit_cents",
        "batch_count",
    )
    list_filter = ("status", "uploaded_at")
    search_fields = ("file_name", "sha256", "immediate_origin", "origin_name")
    ordering = ("-uploaded_at",)
    readonly_fields = ("sha256",)
    inlines = (BatchInline,)


admin.site.register(Batch)
admin.site.register(Entry)
