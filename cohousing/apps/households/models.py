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
from datetime import datetime, timedelta
from decimal import *


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


class Household(models.Model):
    
    long_name = models.CharField(max_length=64)
    short_name = models.CharField(max_length=8)
    slug = models.SlugField("Page name", editable=False)
    member_users = models.ManyToManyField(User, through="HouseholdMember", verbose_name=_('members'))
    
    class Meta:
        ordering = ['short_name',]
    
    def __unicode__(self):
        return self.long_name   
    
    def save(self, force_insert=False, force_update=False):
        unique_slugify(self, self.short_name)
        super(Household, self).save(force_insert, force_update)
        
    @models.permalink
    def get_absolute_url(self):
        return ('household', (), {"household_slug": self.slug})
    
    def has_member(self, user):
        if user.is_authenticated():
            if HouseholdMember.objects.filter(household=self, user=user).count() > 0: # @@@ is there a better way?
                return True
        return False

    @property
    def name(self):
        return self.long_name

        
class HouseholdMember(models.Model):
    
    ROLE_CHOICES = (
        ('owner', 'Owner'), 
        ('builder', 'Owner To Build'),
        ('seller', 'Owner To Sell'), 
        ('resident', 'Resident'),
        ('renter', 'Renter'),
        ('shortterm', 'Short Term Guest'),
        ('longterm', 'Long Term Guest'),
        ('other', 'Other'),
    )
    
    household = models.ForeignKey(Household, related_name="members")
    user = models.ForeignKey(User, related_name="household_membership")
    role = models.CharField(_('function'), max_length=12, choices=ROLE_CHOICES)
    
    class Meta:
        unique_together = ("household", "user")
        
    def user_name(self):
        if self.user.get_full_name():
            return self.user.get_full_name()
        else:
            return self.user.username

