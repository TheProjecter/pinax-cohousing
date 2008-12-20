from django.contrib import admin
from households.models import *

from orgs.fields import UserFullNameChoiceField


class HouseholdMemberInline(admin.TabularInline):
    model = HouseholdMember
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "user":
            return UserFullNameChoiceField(User.objects.all(), label="Person")
        return super(HouseholdMemberInline, self).formfield_for_dbfield(db_field, **kwargs)

class HouseholdAdmin(admin.ModelAdmin):
    list_display = ( "long_name", "short_name")
    inlines = [ HouseholdMemberInline, ]

admin.site.register(Household, HouseholdAdmin)
