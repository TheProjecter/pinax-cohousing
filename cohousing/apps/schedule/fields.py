from django import forms
from django.utils.translation import ugettext_lazy as _
from schedule.models import Event
import datetime
import time

class GlobalSplitDateTimeWidget(forms.SplitDateTimeWidget):
    def __init__(self, hour24 = False, attrs=None, *args, **kwargs):
        """
        hour24 is a boolean. If set to true it will display like a normal
        SplitDateTimeWidget, else it will have a choice for am, pm.
        """
        super(GlobalSplitDateTimeWidget, self).__init__(attrs, *args, **kwargs)
        if not hour24:
            self.widgets = [
                forms.TextInput(attrs=attrs),
                forms.TextInput(attrs=attrs),
                forms.Select(attrs=attrs, choices=[('AM',_('AM')),('PM',_('PM'))]),
            ]
        self.hour24 = hour24
        
    def decompress(self, value):
        if value:
            if self.hour24:
                return super(GlobalSplitDateTimeWidget,self).decompress(value)
            else:
                return [value.date(), value.strftime("%I:%M"), value.strftime("%p")]
        return ""
    
    def value_from_datadict(self, data, files, name):
        if self.hour24:
            return super(GlobalSplitDateTimeWidget,self).value_from_datadict(data, files, name)
        else:
            formats = ['%s %%p' % s.replace('H', 'I') for s in forms.DEFAULT_DATETIME_INPUT_FORMATS]
            data =' '.join([widget.value_from_datadict(data, files, name + '_%s' % i) for i, widget in enumerate(self.widgets)])
            for format in formats:
                try:
                    return datetime.datetime(*time.strptime(data, format)[:6])
                except ValueError:
                    continue
            # raise ValueError('the data given isn\'t properly formatted.')