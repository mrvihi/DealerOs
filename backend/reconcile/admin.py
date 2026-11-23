from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Location, SystemARecord, SystemBEntry, Disagreement


admin.site.register(Location)
admin.site.register(SystemARecord)
admin.site.register(SystemBEntry)
admin.site.register(Disagreement)
