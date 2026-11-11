from django.contrib import admin

from .models import AchFile, Batch, Entry

# Register your models here.
admin.site.register(AchFile)
admin.site.register(Batch)
admin.site.register(Entry)
