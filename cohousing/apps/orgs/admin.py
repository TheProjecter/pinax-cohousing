from django.contrib import admin
#from django import forms
from orgs.models import *

from orgs.fields import UserFullNameChoiceField
#from orgs.forms import OrgPositionForm, MembershipForm

#from django.contrib.admin import widgets 

#class AdminMeetingForm(forms.ModelForm):
#    date_and_time = forms.DateTimeField(widget=widgets.AdminSplitDateTime)
    
#    class Meta:
#        model = Meeting

class MeetingAdmin(admin.ModelAdmin):
#    form = AdminMeetingForm
    list_display = ("org", "name", "description", "date_and_time")

admin.site.register(Meeting, MeetingAdmin)
     

class MembershipInline(admin.TabularInline):
#    form = MemberForm
    model = Membership
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "person":
            return UserFullNameChoiceField(User.objects.all(), label="Person")
        return super(MembershipInline, self).formfield_for_dbfield(db_field, **kwargs)

class PositionTypeAdmin(admin.ModelAdmin):
    list_display = ("slug", "title", "short_name")

admin.site.register(PositionType, PositionTypeAdmin)

    
class OrgPositionInline(admin.TabularInline):
#    form = OrgPositionForm
    model = OrgPosition
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "holder":
            return UserFullNameChoiceField(User.objects.all(), label="Holder", required=False)
        return super(OrgPositionInline, self).formfield_for_dbfield(db_field, **kwargs)

 
class OrgTypeAdmin(admin.ModelAdmin):
    list_display = ("slug", "long_name", "short_name")

admin.site.register(OrgType, OrgTypeAdmin)


class OrgAdmin(admin.ModelAdmin):
    list_display = ( "long_name", "short_name", "parent", "type")
    inlines = [ OrgPositionInline, MembershipInline ]

admin.site.register(Org, OrgAdmin)

class TaskAdmin(admin.ModelAdmin):
    list_display = ("summary", "parent", "assignee", "state")

admin.site.register(Task, TaskAdmin)
