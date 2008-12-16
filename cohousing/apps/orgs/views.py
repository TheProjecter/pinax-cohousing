from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, Http404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q
from django.forms.formsets import formset_factory

from datetime import datetime

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
    org = get_object_or_404(Circle, slug=org_slug)
    is_member = org.has_member(request.user)
    is_officer = org.has_officer(request.user)

    articles = Article.objects.filter(
        content_type=get_ct(org),
        object_id=org.id).order_by('-last_update')
    total_articles = articles.count()
    articles = articles[:5]
        
    total_tasks = org.tasks.count()
    tasks = org.tasks.order_by("-modified")[:10]
    
    aims = org.aims.all()
    
    upcoming_meetings = org.meetings.filter(date_and_time__gte=datetime.now())
    if upcoming_meetings:
        upcoming_meetings = upcoming_meetings[0:1]
    recent_meetings = org.meetings.filter(date_and_time__lt=datetime.now()).order_by("-date_and_time")
    if recent_meetings:
        recent_meetings = recent_meetings[0:1]
        
    return render_to_response("orgs/org.html", {
        "org": org,
        "articles": articles,
        "total_articles": total_articles,
        "total_tasks": total_tasks,
        "tasks": tasks,
        "aims": aims,
        "is_member": is_member,
        "is_officer": is_officer,
        "upcoming_meetings": upcoming_meetings,
        "recent_meetings": recent_meetings,
    }, context_instance=RequestContext(request))


@login_required
def orgs(request):
    orgs = Circle.objects.filter(parent=None)
    return render_to_response("orgs/orgs.html", {
        "orgs": orgs,
    }, context_instance=RequestContext(request))
    
@login_required
def household(request, household_slug):
    household = get_object_or_404(Household, slug=household_slug)
    return render_to_response("orgs/household.html", {
        "household": household,
    }, context_instance=RequestContext(request))
    
@login_required
def households(request):
    orgs = Household.objects.all()
    return render_to_response("orgs/households.html", {
        "households": orgs,
    }, context_instance=RequestContext(request))
    
@login_required
def your_orgs(request):
    orgs = []
    user = request.user
    members = user.circle_membership.all()
    for member in members:
        orgs.append(member.circle)
    return render_to_response("orgs/your_orgs.html", {
        "orgs": orgs,
    }, context_instance=RequestContext(request))
    
@login_required
def meetings(request, org_slug, form_class=MeetingForm,
        template_name="orgs/meetings.html"):
    org = get_object_or_404(Circle, slug=org_slug)
       
    is_officer = org.has_officer(request.user)
    meeting_time = datetime.now()
    init_values = {
        'date_and_time': meeting_time,
    }
    
    if request.user.is_authenticated() and request.method == "POST":
        if request.POST["action"] == "add_meeting":
            meeting_form = form_class(request.POST)
            if meeting_form.is_valid():
                meeting = meeting_form.save(commit=False)
                meeting.circle = org
                meeting.save()
                request.user.message_set.create(message="added meeting '%s'" % meeting.name)
                #if notification:
                #    notification.send(org.member_users.all(), "orgs_new_meeting", {"creator": request.user, "meeting": meeting, "org": org})
                meeting_form = form_class() # @@@ is this the right way to clear it?
        else:
            meeting_form = form_class(initial=init_values)
    else:
        meeting_form = form_class(initial=init_values)
    
    upcoming_meetings = org.meetings.filter(date_and_time__gte=meeting_time)
    recent_meetings = org.meetings.filter(date_and_time__lt=meeting_time).order_by("-date_and_time")
    
    return render_to_response(template_name, {
        "org": org,
        "upcoming_meetings": upcoming_meetings,
        "recent_meetings": recent_meetings,
        "is_officer": is_officer,
        "meeting_form": meeting_form,
    }, context_instance=RequestContext(request))
    
@login_required
def meeting(request, meeting_slug):
    meeting = get_object_or_404(Meeting, slug=meeting_slug)
    topics = meeting.topics.all().order_by("-order")
    is_officer = meeting.circle.has_officer(request.user)
    is_secretary = meeting.circle.has_secretary(request.user)
    is_opleader = False
    op_leader = meeting.circle.op_leader()
    if op_leader:
        is_opleader = op_leader.user.id == request.user.id
        
    if topics:
        last_topic = topics[0]
        init_values = {"order": last_topic.order + 10,}
    else:
        init_values = {"order": 10,}
        
    if request.method == "POST":
        if request.user.is_authenticated():
            if is_officer:
                topic_form = TopicForm(request.POST)
                if topic_form.is_valid():
                    topic = topic_form.save(commit=False)
                    topic.meeting = meeting
                    topic.creator = request.user
                    topic.save()
                    request.user.message_set.create(message="You have created the topic %s" % topic.title)
                    init_values = {"order": int(topic.order) + 10,}
                    topic_form = TopicForm(initial=init_values)
            else:
                request.user.message_set.create(message="You are not an officer and so cannot start a new topic")
                topic_form = TopicForm(initial=init_values)
        else:
            return HttpResponseForbidden()
    else:
        topic_form = TopicForm(initial=init_values)
    
    return render_to_response("orgs/meeting.html", {
        "meeting": meeting,
        "topic_form": topic_form,
        "is_officer": is_officer,
        "is_secretary": is_secretary,
        "is_opleader": is_opleader,
    }, context_instance=RequestContext(request))
    
@login_required
def edit_meeting(request, meeting_slug):
    meeting = get_object_or_404(Meeting, slug=meeting_slug)
    if request.method == "POST":
        meeting_form = MeetingForm(request.POST, instance=meeting)
        if meeting_form.is_valid():
            meeting = meeting_form.save(commit=False)
            meeting.save()                    
            request.user.message_set.create(message="Successfully updated meeting %s" % meeting)
            return HttpResponseRedirect(reverse("meeting_details", kwargs={"meeting_slug": meeting.slug}))
        else:
            meeting_form = MeetingForm(instance=meeting)
    else:
        meeting_form = MeetingForm(instance=meeting)
    
    return render_to_response("orgs/edit_meeting.html", {
        "meeting_form": meeting_form,
        "meeting": meeting,
    }, context_instance=RequestContext(request))


@login_required
def meeting_announcement(request, meeting_slug):
    if request.method == "POST":
        meeting = get_object_or_404(Meeting, slug=meeting_slug)
        creator = request.user.username
        if request.user.get_full_name():
            creator = request.user.get_full_name()
        if notification:
            notification.send(User.objects.all(), "orgs_meeting_announcement", {"creator": creator, "meeting": meeting, "org": meeting.circle})
            request.user.message_set.create(message="Meeting Announcement has been sent")
        return HttpResponseRedirect(request.POST["next"])
    
@login_required
def request_approval(request, meeting_slug):
    if request.method == "POST":
        meeting = get_object_or_404(Meeting, slug=meeting_slug)
        creator = request.user.username
        if request.user.get_full_name():
            creator = request.user.get_full_name()
        if notification:
            if meeting.circle.op_leader():
                notification.send([meeting.circle.op_leader().user,], "orgs_meeting_approval", {"creator": creator, "meeting": meeting, "org": meeting.circle})
                request.user.message_set.create(message="Meeting agenda approval request has been sent")
        return HttpResponseRedirect(request.POST["next"])
    
@login_required
def approve_agenda(request, meeting_slug):
    if request.method == "POST":
        meeting = get_object_or_404(Meeting, slug=meeting_slug)
        meeting.agenda_approved = True
        meeting.save()
        request.user.message_set.create(message="Meeting agenda has been approved")
        return HttpResponseRedirect(request.POST["next"])

@login_required
def attendance(request, meeting_slug):
    meeting = get_object_or_404(Meeting, slug=meeting_slug)
    attendees = meeting.attendance.all()
    attendee_dict = {}
    attendee_list = []
    for attendee in attendees:
        attendee_dict[attendee.member.id] = "attended"
        attendee_list.append({"member": attendee.member, "attended": "X", "role": attendee.get_role_display()})
    members = meeting.circle.members.all()
    for member in members:
        if not member.id in attendee_dict:
            attendee_list.append({"member": member, "attended": "", "role": ""})
    return render_to_response("orgs/attendance.html", {
        "meeting": meeting,
        "attendees": attendee_list
    }, context_instance=RequestContext(request))
    
def create_attendance_forms(meeting):
    org = meeting.circle
    attendees = meeting.attendance.all()
    attendee_dict = {}
    initial_data = []
    for attendee in attendees:
        attendee_dict[attendee.member.id] = "attended"
        if attendee.member.user.get_full_name():
            member_name = attendee.member.user.get_full_name()
        else:
            member_name = attendee.member.user.username
        if attendee.role:
            role = attendee.role
        else:
            role = ""
        dict = {
             "member_id": attendee.member.id,
             "member_name": member_name,
             "member_role": role,
             "attended": True }
        initial_data.append(dict)
    members = org.members.all()
    for member in members:
        if not member.id in attendee_dict:
            if member.user.get_full_name():
                member_name = member.user.get_full_name()
            else:
                member_name = member.user.username
            if member.role:
                role = member.role
            else:
                role = ""
            dict = {
                 "member_id": member.id,
                 "member_name": member_name,
                 "member_role": role,
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
                role = form_data["member_role"]
                attended = form_data["attended"]
                member = CircleMember.objects.get(pk=member_id)
                try:
                    attendance = MeetingAttendance.objects.get(meeting=meeting, member=member)
                    if not attended:
                        attendance.delete()
                except MeetingAttendance.DoesNotExist:
                    if attended:
                        attendance = MeetingAttendance(meeting=meeting, member=member, role=role)
                        attendance.save()
            request.user.message_set.create(message="updated attendance for meeting '%s'" % meeting.name)
            return HttpResponseRedirect(reverse("org_meetings", kwargs={"org_slug": meeting.circle.slug}))
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

def aims(request, slug, form_class=AimForm,
        template_name="orgs/aims.html"):
    org = get_object_or_404(Org, slug=slug)
       
    is_member = org.has_member(request.user)
    
    if request.user.is_authenticated() and request.method == "POST":
        if request.POST["action"] == "add_aim":
            aim_form = form_class(org, request.POST)
            if aim_form.is_valid():
                aim = aim_form.save(commit=False)
                aim.creator = request.user
                aim.org = org
                aim.save()
                request.user.message_set.create(message="added aim '%s'" % aim.name)
                #if notification:
                #    notification.send(org.member_users.all(), "orgs_new_aim", {"creator": request.user, "aim": aim, "org": org})
                aim_form = form_class(org=org) # @@@ is this the right way to clear it?
        else:
            aim_form = form_class(org=org)
    else:
        aim_form = form_class(org=org)
    
    group_by = request.GET.get("group_by")
    aims = org.aims.all()
    
    return render_to_response(template_name, {
        "org": org,
        "aims": aims,
        "group_by": group_by,
        "is_member": is_member,
        "aim_form": aim_form,
    }, context_instance=RequestContext(request))
    
@login_required
def aim(request, aim_slug):
    print "aim view called"
    aim = get_object_or_404(Aim, slug=aim_slug)
    return render_to_response("orgs/aim.html", {
        "aim": aim,
    }, context_instance=RequestContext(request))
    
@login_required
def calendar(request):
    meetings = Meeting.objects.filter(date_and_time__gt=datetime.now())
    return render_to_response("orgs/calendar.html", {
        "meetings": meetings,
    }, context_instance=RequestContext(request))
    
@login_required
def topics(request, meeting_slug, form_class=TopicForm,
        template_name="orgs/topics.html"):
    meeting = get_object_or_404(Meeting, slug=meeting_slug)
       
    is_officer = meeting.circle.has_officer(request.user)
        
    if request.method == "POST":
        if request.user.is_authenticated():
            if is_officer:
                topic_form = form_class(request.POST)
                if topic_form.is_valid():
                    topic = topic_form.save(commit=False)
                    topic.meeting = meeting
                    topic.creator = request.user
                    topic.save()
                    request.user.message_set.create(message="You have created the topic %s" % topic.title)
                    #if notification:
                    #    notification.send(meeting.circle.members.all(), "meeting_new_topic", {"topic": topic})
                    topic_form = form_class() # @@@ is this the right way to reset it?
            else:
                request.user.message_set.create(message="You are not an officer and so cannot start a new topic")
                topic_form = form_class()
        else:
            return HttpResponseForbidden()
    else:
        topic_form = form_class()
    
    return render_to_response(template_name, {
        "meeting": meeting,
        "topic_form": topic_form,
        "is_officer": is_officer,
    }, context_instance=RequestContext(request))

@login_required
def topic(request, id, edit=False, template_name="orgs/topic.html"):
    topic = get_object_or_404(Topic, id=id)
       
    if request.method == "POST" and edit == True and \
        (request.user == topic.creator or request.user == topic.meeting.creator):
        topic.body = request.POST["body"]
        topic.save()
        return HttpResponseRedirect(reverse('meeting_topic', args=[topic.id]))
    return render_to_response(template_name, {
        'topic': topic,
        'edit': edit,
    }, context_instance=RequestContext(request))

@login_required
def topic_delete(request, pk):
    topic = Topic.objects.get(pk=pk)

    if request.method == "POST" and (request.user == topic.creator or request.user == topic.meeting.creator): 
        if forums:
            ThreadedComment.objects.all_for_object(topic).delete()
        topic.delete()
    
    return HttpResponseRedirect(request.POST["next"])

@login_required
def edit_topic(request, pk):
    topic = get_object_or_404(Topic, pk=pk)
    if request.method == "POST":
        topic_form = TopicForm(request.POST, instance=topic)
        if topic_form.is_valid():
            topic = topic_form.save(commit=False)
            topic.save()                    
            request.user.message_set.create(message="Successfully updated meeting agenda topic")
            return HttpResponseRedirect(reverse("meeting_details", kwargs={"meeting_slug": topic.meeting.slug}))
        else:
            topic_form = TopicForm(instance=topic)
    else:
        topic_form = TopicForm(instance=topic)
    
    return render_to_response("orgs/edit_topic.html", {
        "topic_form": topic_form,
        "topic": topic,
    }, context_instance=RequestContext(request))