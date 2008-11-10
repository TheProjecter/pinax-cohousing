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
    if org.type.slug == "hh":
        return render_to_response("orgs/household.html", {
            "household": org,
        }, context_instance=RequestContext(request))
    else:
        articles = Article.objects.filter(
            content_type=get_ct(org),
            object_id=org.id).order_by('-last_update')
        total_articles = articles.count()
        articles = articles[:5]
        
        total_tasks = org.tasks.count()
        tasks = org.tasks.order_by("-modified")[:10]
        return render_to_response("orgs/org.html", {
            "org": org,
            "articles": articles,
            "total_articles": total_articles,
            "total_tasks": total_tasks,
            "tasks": tasks,
        }, context_instance=RequestContext(request))


@login_required
def orgs(request):
    orgs = Org.objects.filter(parent=None).exclude(type__slug="hh")
    #all_orgs = Org.objects.all()
    #nested_orgs = []
    #for org in orgs:
    #    nested_orgs.extend(nested_org_list(org, all_orgs))
    return render_to_response("orgs/orgs.html", {
        "orgs": orgs,
    #    "nested_orgs": nested_orgs,
    }, context_instance=RequestContext(request))
    
@login_required
def households(request):
    orgs = Org.objects.filter(type__slug="hh")
    return render_to_response("orgs/households.html", {
        "households": orgs,
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
        if attendee.member.user.get_full_name():
            member_name = attendee.member.user.get_full_name()
        else:
            member_name = attendee.member.user.username
        dict = {
             "member_id": attendee.member.id,
             "member_name": member_name,
             "member_title": attendee.member.title(),
             "attended": True }
        initial_data.append(dict)
    members = org.members.all()
    for member in members:
        if not member.id in attendee_dict:
            if member.user.get_full_name():
                member_name = member.user.get_full_name()
            else:
                member_name = member.user.username
            dict = {
                 "member_id": member.id,
                 "member_name": member_name,
                 "member_title": member.title(),
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
                member = OrgMember.objects.get(pk=member_id)
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
 
 
def tasks(request, slug, form_class=TaskForm,
        template_name="orgs/tasks.html"):
    org = get_object_or_404(Org, slug=slug)
       
    is_member = org.has_member(request.user)
    
    if request.user.is_authenticated() and request.method == "POST":
        if request.POST["action"] == "add_task":
            task_form = form_class(org, request.POST)
            if task_form.is_valid():
                task = task_form.save(commit=False)
                task.creator = request.user
                task.org = org
                # @@@ we should check that assignee is really a member
                task.save()
                request.user.message_set.create(message="added task '%s'" % task.summary)
                if notification:
                    notification.send(org.member_users.all(), "orgs_new_task", {"creator": request.user, "task": task, "org": org})
                task_form = form_class(org=org) # @@@ is this the right way to clear it?
        else:
            task_form = form_class(org=org)
    else:
        task_form = form_class(org=org)
    
    group_by = request.GET.get("group_by")
    tasks = org.tasks.all()
    
    return render_to_response(template_name, {
        "org": org,
        "tasks": tasks,
        "group_by": group_by,
        "is_member": is_member,
        "task_form": task_form,
    }, context_instance=RequestContext(request))

def task(request, id, template_name="orgs/task.html"):
    task = get_object_or_404(Task, id=id)
    org = task.org
       
    is_member = org.has_member(request.user)
    
    if is_member and request.method == "POST":
        if request.POST["action"] == "assign":
            status_form = StatusForm(instance=task)
            assign_form = AssignForm(org, request.POST, instance=task)
            if assign_form.is_valid():
                task = assign_form.save()
                request.user.message_set.create(message="assigned task to '%s'" % task.assignee)
                if notification:
                    notification.send(org.member_users.all(), "orgs_task_assignment", {"user": request.user, "task": task, "org": org, "assignee": task.assignee})
        elif request.POST["action"] == "update_status":
            assign_form = AssignForm(org, instance=task)
            status_form = StatusForm(request.POST, instance=task)
            if status_form.is_valid():
                task = status_form.save()
                request.user.message_set.create(message="updated your status on the task")
                if notification:
                    notification.send(org.member_users.all(), "orgs_task_status", {"user": request.user, "task": task, "org": org})
        else:
            assign_form = AssignForm(org, instance=task)
            status_form = StatusForm(instance=task)
            if request.POST["action"] == "mark_resolved" and request.user == task.assignee:
                task.state = '2'
                task.save()
                request.user.message_set.create(message="task marked resolved")
                if notification:
                    notification.send(org.member_users.all(), "orgs_task_change", {"user": request.user, "task": task, "org": org, "new_state": "resolved"})
            elif request.POST["action"] == "mark_closed" and request.user == task.creator:
                task.state = '3'
                task.save()
                request.user.message_set.create(message="task marked closed")
                if notification:
                    notification.send(org.member_users.all(), "orgs_task_change", {"user": request.user, "task": task, "org": org, "new_state": "closed"})
            elif request.POST["action"] == "reopen" and is_member:
                task.state = '1'
                task.save()
                request.user.message_set.create(message="task reopened")
                if notification:
                    notification.send(org.member_users.all(), "orgs_task_change", {"user": request.user, "task": task, "org": org, "new_state": "reopened"})
    else:
        assign_form = AssignForm(org, instance=task)
        status_form = StatusForm(instance=task)
    
    return render_to_response(template_name, {
        "task": task,
        "is_member": is_member,
        "assign_form": assign_form,
        "status_form": status_form,
    }, context_instance=RequestContext(request))

def user_tasks(request, username, template_name="orgs/user_tasks.html"):
    other_user = get_object_or_404(User, username=username)
    tasks = other_user.assigned_org_tasks.all().order_by("state")

    return render_to_response(template_name, {
        "tasks": tasks,
        "other_user": other_user,
    }, context_instance=RequestContext(request))
user_tasks = login_required(user_tasks)   