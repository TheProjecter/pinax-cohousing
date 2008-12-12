from django.contrib import admin
#from django import forms
from orgs.models import *

from orgs.fields import UserFullNameChoiceField


class MeetingAdmin(admin.ModelAdmin):
    list_display = ("circle", "name", "location", "description", "date_and_time")

admin.site.register(Meeting, MeetingAdmin)
     

class CircleMemberInline(admin.TabularInline):
    model = CircleMember
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "user":
            return UserFullNameChoiceField(User.objects.all(), label="Person")
        return super(CircleMemberInline, self).formfield_for_dbfield(db_field, **kwargs)

class CircleAdmin(admin.ModelAdmin):
    list_display = ( "long_name", "short_name", "parent")
    inlines = [ CircleMemberInline, ]

admin.site.register(Circle, CircleAdmin)

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

class TaskAssignmentInline(admin.TabularInline):
    model = TaskAssignment
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "user":
            return UserFullNameChoiceField(User.objects.all(), label="Person")
        return super(TaskAssignmentInline, self).formfield_for_dbfield(db_field, **kwargs)
    
class WorkEventInline(admin.TabularInline):
    model = WorkEvent
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == "user":
            return UserFullNameChoiceField(User.objects.all(), label="Person")
        return super(WorkEventInline, self).formfield_for_dbfield(db_field, **kwargs)


class TaskAdmin(admin.ModelAdmin):
    list_display = ("circle", "aim", "summary", "detail", "estimated_duration", "state")
    inlines = [TaskAssignmentInline, WorkEventInline]

admin.site.register(Task, TaskAdmin)

class AimAdmin(admin.ModelAdmin):
    list_display = ("org", "name", "description", "leader", "doer", "evaluator")

admin.site.register(Aim, AimAdmin)
