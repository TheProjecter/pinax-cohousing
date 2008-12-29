from django import forms
from django.utils.translation import ugettext_lazy as _
from schedule.models import Event
from schedule.fields import GlobalSplitDateTimeWidget

import datetime
import time
            

class EventForm(forms.ModelForm):
    def __init__(self, hour24=False, *args, **kwargs):
        """hour24 decides how the datetime widget will be displayed"""
        super(EventForm, self).__init__(*args, **kwargs)
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
        model = Event
        exclude = ('creator', 'created_on')

