from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseForbidden

from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from friends.forms import InviteFriendForm
from friends.models import FriendshipInvitation, Friendship
from photos.models import Image
from schedule.models import Calendar

#from zwitschern.models import Following

from profiles.models import Profile
from profiles.forms import ProfileForm

from avatar.templatetags.avatar_tags import avatar
#from gravatar.templatetags.gravatar import gravatar as avatar

try:
    from notification import models as notification
except ImportError:
    notification = None

def profiles(request, template_name="profiles/profiles.html"):
    users = User.objects.all().order_by("username")
    #for user in users:
    #    if user.get_full_name():
    #        user.fullname = user.get_full_name()
    #    else:
    #        user.fullname= user.username
    #users.sort(lambda x, y: cmp(x.fullname.lower(), y.fullname.lower()))
    return render_to_response(template_name, {
        "users": users,
    }, context_instance=RequestContext(request))

def profile(request, username, template_name="profiles/profile.html"):
    other_user = get_object_or_404(User, username=username)
    profile = other_user.get_profile()
    try:
        cal = Calendar.objects.get(pk=1)
    except Calendar.DoesNotExist:
        cal = Calendar(name="Community Calendar")
        cal.save()
    if request.user.is_authenticated():
        if request.user == other_user:
            is_me = True
        else:
            is_me = False
    else:
        is_me = False
    
    if is_me:
        if request.method == "POST":
            if request.POST["action"] == "update":
                profile_form = ProfileForm(request.POST, instance=other_user.get_profile())
                if profile_form.is_valid():
                    profile = profile_form.save(commit=False)
                    profile.user = other_user
                    profile.save()
            else:
                profile_form = ProfileForm(instance=other_user.get_profile())
        else:
            profile_form = ProfileForm(instance=other_user.get_profile())
    else:
        profile_form = None

    return render_to_response(template_name, {
        "profile_form": profile_form,
        "is_me": is_me,
        "other_user": other_user,
        "profile": profile,
        "calendar": cal,
    }, context_instance=RequestContext(request))

def username_autocomplete(request):
    if request.user.is_authenticated():
        q = request.GET.get("q")
        friends = Friendship.objects.friends_for_user(request.user)
        content = []
        for friendship in friends:
            if friendship["friend"].username.lower().startswith(q):
                try:
                    profile = friendship["friend"].get_profile()
                    entry = "%s,,%s,,%s" % (
                        avatar(friendship["friend"], 40),
                        friendship["friend"].username,
                        profile.location
                    )
                except Profile.DoesNotExist:
                    pass
                content.append(entry)
        response = HttpResponse("\n".join(content))
    else:
        response = HttpResponseForbidden()
    setattr(response, "djangologging.suppress_output", True)
    return response
