from django.conf.urls.defaults import *

from orgs.models import Org
from wiki import models as wiki_models


wiki_args = {
    'group_slug_field': 'slug',
    'group_qs': Org.objects.all(),
    'is_member': (lambda user, group: group.has_member(user)),
    'is_private': False,
}

urlpatterns = patterns('',
    # orgs for the current user
    url(r'^$', 'orgs.views.your_orgs', name="your_orgs"),
    # organization outline (all orgs)
    url(r'orgstructure/$', 'orgs.views.orgs', name="org_structure"),
    # Households
    url(r'households/$', 'orgs.views.households', name="households"),
    # a single organization
    url(r'^org/(?P<org_slug>[-\w]+)/$', 'orgs.views.org', name='organization'),
    # meeting details
    url(r'^meeting/(?P<meeting_slug>[-\w]+)/$', 'orgs.views.meeting', name='meeting_details'),
    # update meeting attendance
    url(r'^attendanceupdate/(?P<meeting_slug>[-\w]+)/$', 'orgs.views.attendance_update', name='update_attendance'),
    # view meeting attendance
    url(r'^attendance/(?P<meeting_slug>[-\w]+)/$', 'orgs.views.attendance', name='meeting_attendance'),
    
    # wiki
    url(r'^org/(?P<group_slug>\w+)/wiki/', include('wiki.urls'), kwargs=wiki_args),
    
    # tasks
    url(r'^org/(\w+)/tasks/$', 'orgs.views.tasks', name="org_tasks"),
    url(r'^task/(\d+)/$', 'orgs.views.task', name="org_task"),
    url(r'^tasks/(\w+)/$', 'orgs.views.user_tasks', name="org_user_tasks")

)
