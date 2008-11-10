from django import forms

from orgs.fields import UserFullNameChoiceField
from orgs.models import *

class OrgPositionForm(forms.ModelForm):
    
    class Meta:
        model = OrgPosition
    
    def __init__(self, *args, **kwargs):
        super(OrgPositionForm, self).__init__(*args, **kwargs)
        self.fields["holder"] = UserFullNameChoiceField(self.fields["holder"].queryset)
        
class OrgMemberForm(forms.ModelForm):
    
    class Meta:
        model = OrgMember
    
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
    member_id = forms.IntegerField(widget=forms.HiddenInput)
    member_name=forms.CharField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '32'}))
    member_title =forms.CharField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '16'}))
    attended=forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'attended',}))
    

class TaskForm(forms.ModelForm):
    def __init__(self, org, *args, **kwargs):
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields["assignee"].queryset = self.fields["assignee"].queryset.filter(org=org)
    
    class Meta:
        model = Task
        fields = ('summary', 'detail', 'assignee', 'tags')


class AssignForm(TaskForm):
    """
    a form for changing the assignee of a task
    """
    class Meta(TaskForm.Meta):
        fields = ('assignee',)


class StatusForm(forms.ModelForm):
    """
    a form for changing the status of a task
    """
    status = forms.CharField(widget=forms.TextInput(attrs={'size':'40'}))
    
    class Meta:
        model = Task
        fields = ('status',)
        

