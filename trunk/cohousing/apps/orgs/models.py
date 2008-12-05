from django.db import models
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from django.utils.encoding import iri_to_uri
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals

from tagging.fields import TagField
from tagging.models import Tag

import re
from datetime import datetime

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


class OrgType(models.Model):
    long_name = models.CharField(max_length=64)
    short_name = models.CharField(max_length=8)
    slug = models.SlugField("Page name", editable=False)
    
    def __unicode__(self):
        return self.long_name   
    
    def save(self, force_insert=False, force_update=False):
        unique_slugify(self, self.short_name)
        super(OrgType, self).save(force_insert, force_update)
        
    @models.permalink
    def get_absolute_url(self):
        return ('orgtype', None, {"orgtype_slug": iri_to_uri(self.slug)})


class Org(models.Model):
    type = models.ForeignKey(OrgType, related_name="orgs", blank=True, null=True)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name="Sponsor")
    long_name = models.CharField(max_length=64)
    short_name = models.CharField(max_length=8)
    slug = models.SlugField("Page name", editable=False)
    member_users = models.ManyToManyField(User, through="OrgMember", verbose_name=_('members'))
    
    class Meta:
        verbose_name = ("Organization")
    
    def __unicode__(self):
        return self.long_name   
    
    def save(self, force_insert=False, force_update=False):
        unique_slugify(self, self.short_name)
        super(Org, self).save(force_insert, force_update)
        
    @models.permalink
    def get_absolute_url(self):
        return ('organization', (), {"org_slug": self.slug})
    
    def has_member(self, user):
        if user.is_authenticated():
            if OrgMember.objects.filter(org=self, user=user).count() > 0: # @@@ is there a better way?
                return True
        return False
    
    def has_officer(self, user):
        if user.is_authenticated():
            if OrgPosition.objects.filter(org=self, holder=user).count() > 0: # @@@ is there a better way?
                return True
        return False

    @property
    def name(self):
        return self.long_name
        
class OrgMember(models.Model):
    org = models.ForeignKey(Org, related_name="members")
    user = models.ForeignKey(User, related_name="org_membership")
    
    class Meta:
        unique_together = ("org", "user")
        
    def user_name(self):
        if self.user.get_full_name():
            return self.user.get_full_name()
        else:
            return self.user.username
        
    def titles(self):
        try:
            positions = self.user.position_holder.filter(org=self.org)
            titles = []
            for pos in positions:
                titles.append(pos.type.title)
            return ", ".join(titles)
        except OrgPosition.DoesNotExist:
            return ""
        
    #def title(self):
    #    try:
    #        position = OrgPosition.objects.get(org=self.org, holder=self.user)
    #        return position.type.title
    #    except OrgPosition.DoesNotExist:
    #        return ""
    
    
class PositionType(models.Model):
    title = models.CharField(max_length=64)
    short_name = models.CharField(max_length=8)
    slug = models.SlugField("Page name", editable=False)
    
    def __unicode__(self):
        return self.title   
    
    def save(self, force_insert=False, force_update=False):
        unique_slugify(self, self.short_name)
        super(PositionType, self).save(force_insert, force_update)
        
    @models.permalink
    def get_absolute_url(self):
        return ('positiontype', (), {"positiontype_slug": iri_to_uri(self.slug)})


    
class OrgPosition(models.Model):
       
    type = models.ForeignKey(PositionType, related_name="positions")
    org = models.ForeignKey(Org, related_name="positions", verbose_name=_('Organization'))
    holder = models.ForeignKey(User, blank=True, null=True, related_name="position_holder")
    slug = models.SlugField("Page name", editable=False)
    
    def __unicode__(self):
        holder_name = "None"
        if self.holder:
            holder_name = self.holder.get_full_name()
            if not holder_name:
                holder_name = self.holder.username
        return " ".join([self.org.short_name, self.type.title, holder_name ])
    
    def save(self, force_insert=False, force_update=False):
        unique_slugify(self, str(self.__unicode__()))
        super(OrgPosition, self).save(force_insert, force_update)
        if self.holder:
            try:
                membership = self.holder.org_membership.get(org=self.org)
            except OrgMember.DoesNotExist:
                mbr = OrgMember(org=self.org, user=self.holder).save()
        
    @models.permalink
    def get_absolute_url(self):
        return ('orgposition', None, {"orgposition_slug": iri_to_uri(self.slug)})
    

class Aim(models.Model):
    org = models.ForeignKey(Org, related_name="aims")
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
    

class Meeting(models.Model):
    org = models.ForeignKey(Org, related_name="meetings")
    name = models.CharField(max_length=64)
    location = models.CharField(max_length=128)
    description = models.TextField()
    date_and_time = models.DateTimeField(default=datetime.now,
        help_text="Time is on a 24-hour clock")
    slug = models.SlugField("Page name", editable=False)
    
    tags = TagField()
    
    class Meta:
        ordering = ['date_and_time']
    
    def __unicode__(self):
        return " ".join([
            self.org.short_name, 
            self.name, 
            self.date_and_time.strftime('%Y-%m-%d') ])
        
    @models.permalink
    def get_absolute_url(self):
        return ('meeting_details', (), {"meeting_slug": self.slug})
        
    def save(self, force_insert=False, force_update=False):
        unique_slugify(self, 
            "-".join([self.org.short_name, 
            self.name,
            self.date_and_time.strftime('%Y-%m-%d')])
            )
        super(Meeting, self).save(force_insert, force_update)
        
class MeetingAttendance(models.Model):
    meeting = models.ForeignKey(Meeting, related_name="attendance")
    member = models.ForeignKey(OrgMember, related_name="meeting_attendance")
    #member = models.ForeignKey(OrgMember, related_name="meeting_attendance", 
    #    limit_choices_to={})
        
    class Meta:
        unique_together = ("meeting", "member")
        
class Topic(models.Model):
    """
    a discussion topic for a meeting.
    """
    
    meeting = models.ForeignKey(Meeting, related_name="topics", verbose_name=_('meeting'))
    
    title = models.CharField(_('title'), max_length=50)
    creator = models.ForeignKey(User, related_name="created_meeting_topics", verbose_name=_('creator'))
    created = models.DateTimeField(_('created'), default=datetime.now)
    modified = models.DateTimeField(_('modified'), default=datetime.now) # topic modified when commented on
    body = models.TextField(_('body'), blank=True)
    
    tags = TagField()
    
    def __unicode__(self):
        return self.title
    
    def get_absolute_url(self):
        return ("meeting_topic", [self.pk])
    get_absolute_url = models.permalink(get_absolute_url)
    
    class Meta:
        ordering = ('modified', )

  
class Task(models.Model):
    """
    a task to be performed for the organizational unit.
    """
    
    STATE_CHOICES = (
        ('1', 'open'),
        ('2', 'resolved'), # the doer thinks it's done
        ('3', 'closed'), # the leader has confirmed it's done
    )
    
    org = models.ForeignKey(Org, related_name="tasks", verbose_name=_('Organization'))
    aim = models.ForeignKey(Aim, blank=True, null=True, related_name="tasks", verbose_name=_('Aim'))
    parent = models.ForeignKey('self', blank=True, null=True, related_name='subtasks')
    summary = models.CharField(_('summary'), max_length=100)
    detail = models.TextField(_('detail'), blank=True)
    creator = models.ForeignKey(User, related_name="created_org_tasks", verbose_name=_('creator'))
    created = models.DateTimeField(_('created'), default=datetime.now)
    modified = models.DateTimeField(_('modified'), default=datetime.now) # task modified when commented on or when various fields changed
    assignee = models.ForeignKey(User, related_name="assigned_org_tasks", verbose_name=_('assignee'), null=True, blank=True)
    
    leader = models.ForeignKey(User, related_name="task_leader", verbose_name=_('leader'), null=True, blank=True)
    doer = models.ForeignKey(User, related_name="task_doer", verbose_name=_('doer'), null=True, blank=True)
    evaluator = models.ForeignKey(User, related_name="task_evaluator", verbose_name=_('evaluator'), null=True, blank=True)
    
    tags = TagField()
    
    # status is a short message the assignee can give on their current status
    status = models.CharField(_('status'), max_length=50, blank=True)
    state = models.CharField(_('state'), max_length=1, choices=STATE_CHOICES, default=1)
    
    def __unicode__(self):
        return self.summary
    
    def save(self, force_insert=False, force_update=False):
        self.modified = datetime.now()
        super(Task, self).save(force_insert, force_update)
    
    @models.permalink
    def get_absolute_url(self):
        return ("org_task", [self.pk])

    
from threadedcomments.models import ThreadedComment
def new_comment(sender, instance, **kwargs):
    if isinstance(instance.content_object, Task):
        task = instance.content_object
        task.modified = datetime.now()
        task.save()
        org = task.org
        if notification:
            notification.send(org.member_users.all(), "orgs_task_comment", {"user": instance.user, "task": task, "org": org, "comment": instance})
signals.post_save.connect(new_comment, sender=ThreadedComment)
