from django.conf.urls.defaults import *

from orgs.models import Circle
from wiki import models as wiki_models


wiki_args = {
    'group_slug_field': 'slug',
    'group_qs': Circle.objects.all(),
    'is_member': (lambda user, group: group.has_member(user)),
    'is_private': False,
}

urlpatterns = patterns('',
    # orgs for the current user
    url(r'^$', 'orgs.views.your_orgs', name="your_orgs"),
    # organization outline (all orgs)
    url(r'orgstructure/$', 'orgs.views.orgs', name="org_structure"),
    # a single organization
    url(r'^org/(?P<org_slug>[-\w]+)/$', 'orgs.views.org', name='organization'),
    
    # all households
    #url(r'households/$', 'orgs.views.households', name="households"),
    # a single households
    #url(r'household/(?P<household_slug>[-\w]+)/$', 'orgs.views.household', name="household"),
    
    #meetings
    url(r'^org/(?P<org_slug>[-\w]+)/meetings/$', 'orgs.views.meetings', name="org_meetings"),
    # meeting details
    url(r'^meeting/(?P<meeting_slug>[-\w]+)/$', 'orgs.views.meeting', name='meeting_details'),
    # meeting details
    url(r'^meeting/(?P<meeting_slug>[-\w]+)/agenda$', 'orgs.views.printable_agenda', name='meeting_agenda'),
    # edit meeting
    url(r'^meeting/edit/(?P<meeting_slug>[-\w]+)/$', 'orgs.views.edit_meeting', name='meeting_edit'),
    # meeting announcement
    url(r'^meeting/announcement/(?P<meeting_slug>[-\w]+)/$', 'orgs.views.meeting_announcement', name='announce_meeting'),
    # meeting agenda approval
    url(r'^meeting/requestapproval/(?P<meeting_slug>[-\w]+)/$', 'orgs.views.request_approval', name='request_agenda_approval'),
    url(r'^meeting/agendaapproval/(?P<meeting_slug>[-\w]+)/$', 'orgs.views.approve_agenda', name='agenda_approval'),
    # update meeting attendance
    url(r'^attendanceupdate/(?P<meeting_slug>[-\w]+)/$', 'orgs.views.attendance_update', name='update_attendance'),
    # view meeting attendance
    url(r'^attendance/(?P<meeting_slug>[-\w]+)/$', 'orgs.views.attendance', name='meeting_attendance'),
    
    #circle events
    url(r'^org/(?P<org_slug>[-\w]+)/circleevents/$', 'orgs.views.circle_events', name="org_events"),
    url(r'^circleevent/edit/(?P<event_id>\d+)/$', 'orgs.views.edit_circle_event', name='edit_circle_event'),
    url(r'^circleevent/(?P<event_id>\d+)/$', 'orgs.views.circle_event', name="circle_event"),
    url(r'^circleevent/delete/(?P<event_id>\d+)/$', 'orgs.views.delete_circle_event', name='delete_circle_event'),
    url(r'^circleevent/announcement/(?P<event_id>\d+)/$', 'orgs.views.circle_event_announcement', name='announce_circle_event'),
    
    # wiki
    url(r'^org/(?P<group_slug>\w+)/wiki/', include('wiki.urls'), kwargs=wiki_args),
    
    # topics
    url(r'^meeting/(?P<meeting_slug>[-\w]+)/topics/$', 'orgs.views.topics', name="meeting_topics"),
    url(r'^topic/(\d+)/edit/$', 'orgs.views.edit_topic', name="meeting_topic_edit"),
    url(r'^topic/(\d+)/delete/$', 'orgs.views.topic_delete', name="meeting_topic_delete"),
    url(r'^topic/(\d+)/$', 'orgs.views.topic', name="meeting_topic"),
    
    # tasks
    url(r'^org/(\w+)/tasks/$', 'orgs.views.tasks', name="org_tasks"),
    url(r'^task/(\d+)/$', 'orgs.views.task', name="org_task"),
    url(r'^tasks/(\w+)/$', 'orgs.views.user_tasks', name="org_user_tasks"),
    
    # aims
    url(r'^org/(\w+)/aims/$', 'orgs.views.aims', name="org_aims"),
    url(r'^aim/(?P<aim_slug>[-\w]+)/$', 'orgs.views.aim', name="org_aim"),
    
    # Community calendar
    url(r'calendar/$', 'orgs.views.calendar', name="community_calendar"),
    
    # User Profiles
    url(r'profile/create/$', 'orgs.views.create_user_and_profile', name="create_user_profile"),

)
