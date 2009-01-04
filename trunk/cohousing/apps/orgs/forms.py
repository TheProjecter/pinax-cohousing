from django import forms

from orgs.fields import UserFullNameChoiceField
from orgs.models import *
from schedule.fields import GlobalSplitDateTimeWidget
from schedule.forms import EventForm

from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _

class UserAndProfileCreationForm(UserCreationForm):
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': '50'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': '50'}))
    email = forms.EmailField(required=False, widget=forms.TextInput(attrs={'size': '80'}))
    home_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': '50'}))
    work_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': '50'}))
    cell_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'size': '50'}))


class OrgMemberForm(forms.ModelForm):
    
    class Meta:
        model = CircleMember
    
    def __init__(self, *args, **kwargs):
        super(OrgMemberForm, self).__init__(*args, **kwargs)
        self.fields["user"] = UserFullNameChoiceField(self.fields["user"].queryset, label="Person")
        
    def clean(self):
        cleaned_data = self.cleaned_data
        org = cleaned_data.get("org")
        user = cleaned_data.get("user")
        try:
            member = OrgMember.objects.get(org=org, user=user)
            raise forms.ValidationError("Member already exists")
        except OrgMember.DoesNotExist:
            pass
        super(OrgMemberForm, self).clean()
        return self.cleaned_data


class MeetingAttendanceForm(forms.Form):
    
    FORM_CHOICES = list(MeetingAttendance.ROLE_CHOICES)
    FORM_CHOICES.insert(0, ("", "----------"))
    FORM_CHOICES = tuple(FORM_CHOICES)
    
    member_id = forms.IntegerField(widget=forms.HiddenInput)
    member_name=forms.CharField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '32'}))
    member_role =forms.CharField(required=False, widget=forms.Select(choices=FORM_CHOICES))
    attended=forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'attended',}))
    

class TaskForm(forms.ModelForm):
    def __init__(self, org, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        #self.fields["assignee"].queryset = self.fields["assignee"].queryset.filter(org=org)
    
    class Meta:
        model = Task
        fields = ('summary', 'detail', 'estimated_duration', 'tags')


class TaskAssignmentForm(forms.ModelForm):
    def __init__(self, org, *args, **kwargs):
        super(TaskAssignmentForm, self).__init__(*args, **kwargs)
        self.fields["user"].queryset = self.fields["u"].queryset.filter(org=org)
    
    class Meta:
        model = TaskAssignment
        fields = ('user', 'role', 'state')
        
        
class WorkEventForm(forms.ModelForm):
    def __init__(self, org, *args, **kwargs):
        super(WorkEventForm, self).__init__(*args, **kwargs)
        self.fields["user"].queryset = self.fields["u"].queryset.filter(org=org)
    
    class Meta:
        model = WorkEvent
        fields = ('task_assignment', 'user', 'hours')
            

class AimForm(forms.ModelForm):
    def __init__(self, org, *args, **kwargs):
        super(AimForm, self).__init__(*args, **kwargs)
        self.fields["leader"].queryset = self.fields["leader"].queryset.filter(org=org)
        self.fields["doer"].queryset = self.fields["doer"].queryset.filter(org=org)
        self.fields["evaluator"].queryset = self.fields["evaluator"].queryset.filter(org=org)
    
    class Meta:
        model = Aim
        exclude = ("org", "slug", "creator", "created", "modified")


class MeetingForm(forms.ModelForm):
    alternate_location=forms.CharField(required=False, widget=forms.TextInput(attrs={'size': '100'}))
    date_and_time = forms.DateTimeField(widget=GlobalSplitDateTimeWidget)
   
    class Meta:
        model = Meeting
        fields = ("name", "household_location", "alternate_location", "date_and_time", "tags")

       
class TopicForm(forms.ModelForm):
    order=forms.CharField(widget=forms.TextInput(attrs={'size': '4'}))
    title=forms.CharField(widget=forms.TextInput(attrs={'size': '64'}))
    
    class Meta:
        model = Topic
        fields = ('order', 'title', 'lead',)
        
class CircleEventForm(forms.ModelForm):
    def __init__(self, hour24=False, *args, **kwargs):
        """hour24 decides how the datetime widget will be displayed"""
        super(CircleEventForm, self).__init__(*args, **kwargs)
        if hour24:
            self.fields['start'].widget = GlobalSplitDateTimeWidget(hour24=True)
            self.fields['end'].widget = GlobalSplitDateTimeWidget(hour24=True)
            self.fields['end_recurring_period'].widget = GlobalSplitDateTimeWidget(hour24=True)
    
    start = forms.DateTimeField(widget=GlobalSplitDateTimeWidget)
    end = forms.DateTimeField(widget=GlobalSplitDateTimeWidget,
                help_text = _("The end time must be later than start time."))
    end_recurring_period = forms.DateTimeField(required=False, widget=GlobalSplitDateTimeWidget,
                help_text = _("This date is ignored for one time only events."))
    alternate_location=forms.CharField(required=False, widget=forms.TextInput(attrs={'size': '60'}))
    
    class Meta:
        model = CircleEvent
        exclude = ("circle", "creator", "created_on")