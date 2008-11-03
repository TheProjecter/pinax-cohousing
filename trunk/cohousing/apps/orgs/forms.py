from django import forms

from orgs.fields import UserFullNameChoiceField
from orgs.models import *

class OrgPositionForm(forms.ModelForm):
    
    class Meta:
        model = OrgPosition
    
    def __init__(self, *args, **kwargs):
        super(OrgPositionForm, self).__init__(*args, **kwargs)
        self.fields["holder"] = UserFullNameChoiceField(self.fields["holder"].queryset)
        
class MembershipForm(forms.ModelForm):
    
    class Meta:
        model = Membership
    
    def __init__(self, *args, **kwargs):
        super(MembershipForm, self).__init__(*args, **kwargs)
        self.fields["person"] = UserFullNameChoiceField(self.fields["person"].queryset, label="Person")
        
    def clean(self):
        cleaned_data = self.cleaned_data
        org = cleaned_data.get("org")
        person = cleaned_data.get("person")
        try:
            member = Membership.objects.get(org=org, person=person)
            raise forms.ValidationError("Member already exists")
        except Membership.DoesNotExist:
            pass
        super(MembershipForm, self).clean()
        return self.cleaned_data


class MeetingAttendanceForm(forms.Form):
    member_id = forms.IntegerField(widget=forms.HiddenInput)
    member_name=forms.CharField(widget=forms.TextInput(attrs={'readonly':'true', 'class': 'read-only-input', 'size': '49'}))
    attended=forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'attended',}))
    

