from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.encoding import iri_to_uri
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals
from django.core.urlresolvers import reverse

from tagging.fields import TagField
from tagging.models import Tag
from households.models import *
from schedule.models import Event, EventRelation, Calendar

import re
from datetime import datetime, timedelta
from decimal import *

try:
    from notification import models as notification
except ImportError:
    notification = None

def unique_slugify(instance, value, slug_field_name='slug', queryset=None,
                   slug_separator='-'):
    """
    Calculates a unique slug of ``value`` for an instance.

    ``slug_field_name`` should be a string matching the name of the field to
    store the slug in (and the field to check against for uniqueness).

    ``queryset`` usually doesn't need to be explicitly provided - it'll default
    to using the ``.all()`` queryset from the model's default manager.
    """
    slug_field = instance._meta.get_field(slug_field_name)

    slug = getattr(instance, slug_field.attname)
    slug_len = slug_field.max_length

    # Sort out the initial slug. Chop its length down if we need to.
    slug = slugify(value)
    if slug_len:
        slug = slug[:slug_len]
    slug = _slug_strip(slug, slug_separator)
    original_slug = slug

    # Create a queryset, excluding the current instance.
    if not queryset:
        queryset = instance.__class__._default_manager.all()
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)

    # Find a unique slug. If one matches, at '-2' to the end and try again
    # (then '-3', etc).
    next = 2
    while not slug or queryset.filter(**{slug_field_name: slug}):
        slug = original_slug
        end = '-%s' % next
        if slug_len and len(slug) + len(end) > slug_len:
            slug = slug[:slug_len-len(end)]
            slug = _slug_strip(slug, slug_separator)
        slug = '%s%s' % (slug, end)
        next += 1

    setattr(instance, slug_field.attname, slug)


def _slug_strip(value, separator=None):
    """
    Cleans up a slug by removing slug separator characters that occur at the
    beginning or end of a slug.

    If an alternate separator is used, it will also replace any instances of
    the default '-' separator with the new separator.
    """
    if separator == '-' or not separator:
        re_sep = '-'
    else:
        re_sep = '(?:-|%s)' % re.escape(separator)
        value = re.sub('%s+' % re_sep, separator, value)
    return re.sub(r'^%s+|%s+$' % (re_sep, re_sep), '', value)


class Circle(models.Model):
    
    OFFICERS = ["opleader", "secretary", "opsec", "recordkeeper"]
       
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name="Sponsor")
    long_name = models.CharField(max_length=64)
    short_name = models.CharField(max_length=8)
    slug = models.SlugField("Page name", editable=False)
    #needed 2 fkeys to Circle in CircleMember, so M2M through wd no longer work
    #member_users = models.ManyToManyField(User, through="CircleMember", verbose_name=_('members'))
    
    
    def __unicode__(self):
        return self.long_name   
    
    def save(self, force_insert=False, force_update=False):
        unique_slugify(self, self.short_name)
        super(Circle, self).save(force_insert, force_update)
        
    @models.permalink
    def get_absolute_url(self):
        return ('organization', (), {"org_slug": self.slug})
    
    def member_users(self):
        members = self.members.all()
        users = []
        for member in members:
            users.append(member.user)
        return users
    
    def has_member(self, user):
        if user.is_authenticated():
            if CircleMember.objects.filter(circle=self, user=user).count() > 0: # @@@ is there a better way?
                return True
        return False
    
    def has_officer(self, user):
        if user.is_authenticated():
            try:
                member = CircleMember.objects.get(circle=self, user=user)
                if member.role in self.OFFICERS:
                    return True
                else:
                    return False
            except CircleMember.DoesNotExist:
                return False
        else:
            return False
        
    def has_secretary(self, user):
        if user.is_authenticated():
            try:
                member = CircleMember.objects.get(circle=self, user=user)
                if member.role in ["secretary", "recordkeeper", "opsec"]:
                    return True
                else:
                    return False
            except CircleMember.DoesNotExist:
                return False
        else:
            return False
        
    def officers(self):
        members = CircleMember.objects.filter(circle=self)
        officers = []
        for member in members:
            if member.role in self.OFFICERS:
                officers.append(member)
        return officers
    
    def op_leader(self):
        members = CircleMember.objects.filter(circle=self, role="opleader")
        if members:
            return members[0]
        else:
            return None
        
    def op_leader_secretary(self):
        members = CircleMember.objects.filter(circle=self, role="opsec")
        if members:
            return members[0]
        else:
            return None


    @property
    def name(self):
        return self.long_name

        
class CircleMember(models.Model):
    
    ROLE_CHOICES = (
        ('opleader', 'Operations Leader'), 
        ('secretary', 'Secretary'),
        ('circlerep', 'Circle Representative'),
        ('opsec', 'Op Leader-Secretary'), 
        ('facilitator', 'Facilitator'),
        ('recordkeeper', 'Record Keeper'),
        ('expert', 'Invited Expert'),
        ('eventcoord', 'Event Coordinator'),
    )
    
    TYPE_CHOICES = (
        (1, 'Sponsored Op Leader'),
        (2, 'Circle Rep'), 
        (3, 'HOA President'),
        (4, 'HOA Treasurer'),
        (5, 'HOA Secretary'),
    )
    
    circle = models.ForeignKey(Circle, related_name="members")
    user = models.ForeignKey(User, related_name="circle_membership")
    role = models.CharField(_('function'), max_length=12, choices=ROLE_CHOICES, blank=True)
    type = models.IntegerField(_('type'), choices=TYPE_CHOICES, null=True, blank=True)
    related_circle = models.ForeignKey(Circle, related_name="reps", null=True, blank=True)
    
    class Meta:
        unique_together = ("circle", "user")
        ordering = ['-role', "-related_circle", "-type"]
        
    def user_name(self):
        if self.user.get_full_name():
            return self.user.get_full_name()
        else:
            return self.user.username

    
class Aim(models.Model):
    org = models.ForeignKey(Circle, related_name="aims")
    name = models.CharField(max_length=64)
    description = models.TextField()
    slug = models.SlugField("Page name", editable=False)
    creator = models.ForeignKey(User, related_name="created_aims", verbose_name=_('creator'))
    created = models.DateTimeField(_('created'), default=datetime.now)
    modified = models.DateTimeField(_('modified'), default=datetime.now)
    leader = models.ForeignKey(User, related_name="aim_leader", verbose_name=_('leader'), null=True, blank=True)
    doer = models.ForeignKey(User, related_name="aim_doer", verbose_name=_('doer'), null=True, blank=True)
    evaluator = models.ForeignKey(User, related_name="aim_evaluator", verbose_name=_('evaluator'), null=True, blank=True)
    
    tags = TagField()
    
    class Meta:
        ordering = ['name']
    
    def __unicode__(self):
        return " ".join([
            self.org.short_name, 
            self.name])
        
    @models.permalink
    def get_absolute_url(self):
        return ('org_aim', (), {"aim_slug": self.slug})
    
    def save(self, force_insert=False, force_update=False):
        unique_slugify(self, 
            "-".join([self.org.short_name, 
            self.name,])
            )
        super(Aim, self).save(force_insert, force_update)
    
    
class CircleEvent(Event):
    circle = models.ForeignKey(Circle, related_name="events")
    
    def start_date(self):
        return self.start.date()
    
    def start_time(self):
        return self.start.time()
    
    def common_timestamp(self):
        return self.start
    
    def common_description(self):
        return self.title
    
    def save(self, force_insert=False, force_update=False):
        super(CircleEvent, self).save(force_insert, force_update)
        try:
            cal = Calendar.objects.get(pk=1)
        except Calendar.DoesNotExist:
            cal = Calendar(name="Community Calendar")
            cal.save()
        cal.events.add(self)
        
    def get_absolute_url(self):
        return reverse('circle_event', args=[self.id])

class Meeting(models.Model):
    
    NAME_CHOICES = (
        ('regular', 'Regular Meeting'),
        ('special', 'Special Meeting'),
    )
    
    circle = models.ForeignKey(Circle, related_name="meetings")
    name = models.CharField(max_length=64, choices=NAME_CHOICES, default="regular")
    date_and_time = models.DateTimeField(default=datetime.now)
    household_location = models.ForeignKey(Household, blank=True, null=True)
    alternate_location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    duration = models.IntegerField(default=90,
        help_text="in minutes", blank=True, null=True)
    agenda_approved = models.BooleanField(default=False, blank=True, null=True)
    slug = models.SlugField("Page name", editable=False)
    
    tags = TagField()
    
    class Meta:
        ordering = ['date_and_time']
    
    def __unicode__(self):
        return " ".join([
            self.circle.short_name, 
            self.name, 
            self.date_and_time.strftime('%Y-%m-%d') ])
        
    @models.permalink
    def get_absolute_url(self):
        return ('meeting_details', (), {"meeting_slug": self.slug})
    
    def start_date(self):
        return self.date_and_time.date()
    
    def start_time(self):
        return self.date_and_time.time()
    
    def common_timestamp(self):
        return self.date_and_time
    
    def common_description(self):
        return self.get_name_display()
         
    def location(self):
        if self.household_location:
            return self.household_location
        else:
            return self.alternate_location
        
    def save(self, force_insert=False, force_update=False):
        new_meeting = False
        if not self.id:
            new_meeting = True
        unique_slugify(self, 
            "-".join([self.circle.short_name, 
            self.name,
            self.date_and_time.strftime('%Y-%m-%d')])
            )
        super(Meeting, self).save(force_insert, force_update)
        end = self.date_and_time + timedelta(minutes=self.duration)
        title = " ".join([self.circle.short_name, self.get_name_display()])
        if new_meeting:            
            event = Event(
                          start=self.date_and_time, 
                          end=end, 
                          title=title,
                          household_location=self.household_location,
                          alternate_location=self.alternate_location,
                          description=self.description)
            event.save()
            rel = EventRelation.objects.create_relation(event, self)
            rel.save()
            try:
                cal = Calendar.objects.get(pk=1)
            except Calendar.DoesNotExist:
                cal = Calendar(name="Community Calendar")
                cal.save()
            cal.events.add(event)
        else:
            event = Event.objects.get_for_object(self)[0]
            event.start = self.date_and_time
            event.end = end
            event.title = title
            event.household_location = self.household_location
            event.alternate_location = self.alternate_location
            event.description = self.description
            event.save()
            
    def delete(self):
        try:
            event = Event.objects.get_for_object(self)[0]
        except:
            event = None
        super(Meeting, self).delete()
        if event:
            event.delete()
        
        
class MeetingAttendance(models.Model):
    
    ROLE_CHOICES = (
        ('opleader', 'Operations Leader'), 
        ('secretary', 'Secretary'),
        ('opsec', 'Op Leader-Secretary'), 
        ('facilitator', 'Facilitator'),
        ('recordkeeper', 'Record Keeper'),
    )
    
    meeting = models.ForeignKey(Meeting, related_name="attendance")
    member = models.ForeignKey(CircleMember, related_name="meeting_attendance")
    role = models.CharField(_('function'), max_length=12, choices=ROLE_CHOICES, blank=True)
    
    class Meta:
        unique_together = ("meeting", "member")

        
class Topic(models.Model):
    """
    a discussion topic for a meeting.
    """
    
    ACTION_CHOICES = (
        ('approved', 'Approved'),
        ('withdrawn', 'Withdrawn'),
        ('tabled', 'Tabled'),
    )
    
    meeting = models.ForeignKey(Meeting, related_name="topics", verbose_name=_('meeting'))
    
    order = models.IntegerField(_('order'))
    title = models.CharField(_('title'), max_length=128)
    creator = models.ForeignKey(User, related_name="created_meeting_topics", verbose_name=_('creator'))
    lead = models.ForeignKey(User, related_name="lead_meeting_topics", verbose_name=_('lead'), blank=True, null=True)
    created = models.DateTimeField(_('created'), default=datetime.now)
    modified = models.DateTimeField(_('modified'), default=datetime.now) # topic modified when commented on
    body = models.TextField(_('body'), blank=True)
    action = models.CharField(max_length=12, choices=ACTION_CHOICES, blank=True)
    
    tags = TagField()
    
    class Meta:
        ordering = ('order', )
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        return ("meeting_topic", [self.pk])
    get_absolute_url = models.permalink(get_absolute_url)
    
    class Meta:
        ordering = ('order', )
        
    def lead_name(self):
        if self.lead.get_full_name():
            return self.lead.get_full_name()
        else:
            return self.lead.username

  
class Task(models.Model):
    """
    a task to be performed for a Circle.
    """
    
    STATE_CHOICES = (
        (1, 'open'),
        (2, 'resolved'), # the doer thinks it's done
        (3, 'closed'), # the leader has confirmed it's done
    )
    
    circle = models.ForeignKey(Circle, related_name="tasks", verbose_name=_('Circle'))
    aim = models.ForeignKey(Aim, blank=True, null=True, related_name="tasks", verbose_name=_('Aim'))
    #parent = models.ForeignKey('self', blank=True, null=True, related_name='subtasks')
    summary = models.CharField(_('summary'), max_length=100)
    detail = models.TextField(_('detail'), blank=True)
    estimated_duration = models.IntegerField(help_text='in minutes')
    creator = models.ForeignKey(User, related_name="created_circle_tasks", verbose_name=_('creator'))
    created = models.DateTimeField(_('created'), default=datetime.now)
    modified = models.DateTimeField(_('modified'), default=datetime.now) # task modified when commented on or when various fields changed
    #assignee = models.ForeignKey(User, related_name="assigned_circle_tasks", verbose_name=_('assignee'), null=True, blank=True)
    state = models.IntegerField(_('state'), choices=STATE_CHOICES, default=1)
    
    tags = TagField()
    
    def __unicode__(self):
        return self.summary
    
    def save(self, force_insert=False, force_update=False):
        self.modified = datetime.now()
        super(Task, self).save(force_insert, force_update)
    
    @models.permalink
    def get_absolute_url(self):
        return ("circle_task", [self.pk])
    
    
class TaskAssignment(models.Model):
    """
    a user's assignment to play a role on a task.
    """
     
    ROLE_CHOICES = (
        ('leader-doer', 'Leader-Doer'),
        ('leader', 'Leader'), 
        ('doer', 'Doer'),
        #('evaluator', 'Evaluator'),
    )
    
    STATE_CHOICES = (
        (1, 'open'),
        (2, 'started'),
        (3, 'finished'), 
    )
    
    task = models.ForeignKey(Task, related_name="assignments")
    user = models.ForeignKey(User, related_name="task_assignments")
    role = models.CharField(_('function'), max_length=12, choices=ROLE_CHOICES, default="leader-doer")
    state = models.IntegerField(_('state'), choices=STATE_CHOICES, default=1)
    
    
class WorkEvent(models.Model):
    """
    a user's record of some work on a task.
    """
    
    task = models.ForeignKey(Task, related_name="work_events")
    task_assignment = models.ForeignKey(TaskAssignment, related_name="work_events")
    user = models.ForeignKey(User, related_name="work_events")
    minutes =  models.IntegerField()
    date = models.DateField(default=datetime.now)

    
from threadedcomments.models import ThreadedComment
def new_comment(sender, instance, **kwargs):
    if isinstance(instance.content_object, Task):
        task = instance.content_object
        task.modified = datetime.now()
        task.save()
        org = task.circle
        if notification:
            notification.send(org.member_users(), "orgs_task_comment", {"user": instance.user, "task": task, "org": org, "comment": instance})
signals.post_save.connect(new_comment, sender=ThreadedComment)