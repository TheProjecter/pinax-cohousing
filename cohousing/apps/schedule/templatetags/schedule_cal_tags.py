""" Experimental template tags for django-schedule calendar rendering are herein.
"""

import datetime
from django import template
from django.utils.dates import WEEKDAYS, WEEKDAYS_ABBR
from django.core.urlresolvers import reverse

register = template.Library()

day_names = [WEEKDAYS[6], WEEKDAYS[0], WEEKDAYS[1], WEEKDAYS[2],
             WEEKDAYS[3], WEEKDAYS[4], WEEKDAYS[5]]
abbr_day_names = [WEEKDAYS_ABBR[6], WEEKDAYS_ABBR[0], WEEKDAYS_ABBR[1], WEEKDAYS_ABBR[2],
                  WEEKDAYS_ABBR[3], WEEKDAYS_ABBR[4], WEEKDAYS_ABBR[5]]

@register.inclusion_tag("schedule/_month_table.html")
def month_table( calendar, date, size="regular", uname=None ):
    month = calendar.get_month( date=date )
    if size == "small":
        context = {'day_names':abbr_day_names}
    else:
        context = {'day_names':day_names}
    if uname:
        prev_url_context = { 'calendar_id': calendar.id,
                             'year': month.prev_month().year,
                             'month': month.prev_month().month
                           }
        context['prev_url'] = reverse( uname, kwargs=prev_url_context )
        next_url_context = { 'calendar_id': calendar.id,
                             'year': month.next_month().year,
                             'month': month.next_month().month
                           }
        context['next_url'] = reverse( uname, kwargs=next_url_context )
    context['calendar'] = calendar
    context['month'] = month
    context['size'] = size
    return context

@register.inclusion_tag("schedule/_day_cell.html")
def day_cell( calendar, day, month, size="regular" ):
    return {
        'calendar' : calendar,
        'day' : day,
        'month' : month,
        'size' : size
    }

@register.inclusion_tag("schedule/_daily_table.html")
def daily_table( calendar, day ):
    td30 = datetime.timedelta(minutes=30)
    morning = day.start
    afternoon = day.start  + datetime.timedelta(hours=12)
    morning_period = day.get_time_slot( morning, morning + td30 )
    afternoon_period = day.get_time_slot( afternoon, afternoon + td30 )
    day_slots = [ (morning_period, afternoon_period) ]
    for i in range(23):
        morning += td30
        afternoon += td30
        morning_period = day.get_time_slot( morning, morning + td30 )
        afternoon_period = day.get_time_slot( afternoon, afternoon + td30 )
        day_slots.append( (morning_period, afternoon_period) )
    context = {
        'calendar' : calendar,
        'day' : day,
        'day_slots' : day_slots
    }
    prev_day = day.prev_day()
    prev_url_context = { 'calendar_id': calendar.id,
                         'year': prev_day.year,
                         'month': prev_day.month,
                         'day': prev_day.day
                       }
    context['prev_url'] = reverse( "d_calendar_date", kwargs=prev_url_context )
    next_day = day.next_day()
    next_url_context = { 'calendar_id': calendar.id,
                         'year': next_day.year,
                         'month': next_day.month,
                         'day': next_day.day
                        }
    context['next_url'] = reverse( "d_calendar_date", kwargs=next_url_context )
    return context

@register.inclusion_tag("schedule/_event_options.html")
def title_and_options( event ):
    context = {
        'event' : event
    }
    lookup_context = {
        'event_id': event.id
    }
    context['view_event'] = reverse( "s_event", kwargs=lookup_context )
    context['edit_event'] = reverse( "s_edit_event", kwargs=lookup_context )
    context['delete_event'] = reverse( "s_delete_event", kwargs=lookup_context )
    return context

@register.inclusion_tag("schedule/_create_event_options.html")
def create_event_url( calendar, slot ):
    context = {
        'calendar' : calendar
    }
    lookup_context = {
        'calendar_id': calendar.id,
        'year' : slot.year,
        'month' : slot.month,
        'day' : slot.day,
        'hour' : slot.hour,
        'minute' : slot.minute
    }
    context['create_event_url'] = reverse( "s_create_event_date", kwargs=lookup_context )
    return context
