from django import forms

class UserFullNameChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.get_full_name():
            return obj.get_full_name()
        else:
            return obj.username

