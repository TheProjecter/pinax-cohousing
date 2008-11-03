from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q
from django.forms.formsets import formset_factory

from orgs.models import *
from orgs.forms import *

try:
    from notification import models as notification
except ImportError:
    notification = None

try:
    from threadedcomments.models import ThreadedComment
    forums = True
except ImportError:
    forums = False

try:
    from wiki.models import Article
    from wiki.views import get_ct
    wiki = True
except ImportError:
    wiki = False

# based on dfs from threaded_comments
def nested_org_list(node, all_nodes):
     to_return = [node,]
     for subnode in all_nodes:
         if subnode.parent and subnode.parent.id == node.id:
             to_return.extend([nested_org_list(subnode, all_nodes),])
     return to_return


@login_required
def org(request, org_slug):
    org = get_object_or_404(Org, slug=org_slug)
    articles = Article.objects.filter(
        content_type=get_ct(org),
        object_id=org.id).order_by('-last_update')
    total_articles = articles.count()
    articles = articles[:5]
    return render_to_response("orgs/org.html", {
        "org": org,
        "articles": articles,
        "total_articles": total_articles,
    }, context_instance=RequestContext(request))


@login_required
def orgs(request):
    orgs = Org.objects.filter(parent=None)
    #all_orgs = Org.objects.all()
    #nested_orgs = []
    #for org in orgs:
    #    nested_orgs.extend(nested_org_list(org, all_orgs))
    return render_to_response("orgs/orgs.html", {
        "orgs": orgs,
    #    "nested_orgs": nested_orgs,
    }, context_instance=RequestContext(request))
    
@login_required
def your_orgs(request):
    orgs = []
    user = request.user
    members = user.org_membership.all()
    for member in members:
        orgs.append(member.org)
    return render_to_response("orgs/your_orgs.html", {
        "orgs": orgs,
    }, context_instance=RequestContext(request))
    
@login_required
def meeting(request, meeting_slug):
    meeting = get_object_or_404(Meeting, slug=meeting_slug)
    return render_to_response("orgs/meeting.html", {
        "meeting": meeting,
    }, context_instance=RequestContext(request))


@login_required
def attendance(request, meeting_slug):
    meeting = get_object_or_404(Meeting, slug=meeting_slug)
    attendees = meeting.attendance.all()
    attendee_dict = {}
    attendee_list = []
    for attendee in attendees:
        attendee_dict[attendee.member.id] = "attended"
        attendee_list.append({"member": attendee.member, "attended": "X"})
    members = meeting.org.members.all()
    for member in members:
        if not member.id in attendee_dict:
            attendee_list.append({"member": member, "attended": ""})
    return render_to_response("orgs/attendance.html", {
        "meeting": meeting,
        "attendees": attendee_list
    }, context_instance=RequestContext(request))
    
def create_attendance_forms(meeting):
    org = meeting.org
    attendees = meeting.attendance.all()
    attendee_dict = {}
    initial_data = []
    for attendee in attendees:
        attendee_dict[attendee.member.id] = "attended"
        if attendee.member.person.get_full_name():
            member_name = attendee.member.person.get_full_name()
        else:
            member_name = attendee.member.person.username
        dict = {
             "member_id": attendee.member.id,
             "member_name": member_name,
             "attended": True }
        initial_data.append(dict)
    members = org.members.all()
    for member in members:
        if not member.id in attendee_dict:
            if member.person.get_full_name():
                member_name = member.person.get_full_name()
            else:
                member_name = member.person.username
            dict = {
                 "member_id": member.id,
                 "member_name": member_name,
                 "attended": False }
            initial_data.append(dict)
    AttendanceFormSet = formset_factory(MeetingAttendanceForm, extra=0)
    return AttendanceFormSet(initial=initial_data)


@login_required
def attendance_update(request, meeting_slug):
    meeting = get_object_or_404(Meeting, slug=meeting_slug)
    
    if request.method == "POST":
        meeting_id = request.POST["meeting_id"]
        meeting = Meeting.objects.get(pk=meeting_id)
        AttendanceFormSet = formset_factory(MeetingAttendanceForm, extra=0)
        formset = AttendanceFormSet(request.POST)
        if formset.is_valid():
            for form in formset.forms:
                form_data = form.cleaned_data
                member_id = form_data["member_id"]
                attended = form_data["attended"]
                member = Membership.objects.get(pk=member_id)
                try:
                    attendance = MeetingAttendance.objects.get(meeting=meeting, member=member)
                    if not attended:
                        attendance.delete()
                except MeetingAttendance.DoesNotExist:
                    if attended:
                        attendance = MeetingAttendance(meeting=meeting, member=member)
                        attendance.save()
            return HttpResponseRedirect(reverse("organization", kwargs={"org_slug": meeting.org.slug}))
    else:
        formset = create_attendance_forms(meeting)

    return render_to_response("orgs/attendance_update.html", {
        "formset": formset,
        "meeting": meeting
    }, context_instance=RequestContext(request))
    