from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from households.models import *

@login_required
def household(request, household_slug):
    household = get_object_or_404(Household, slug=household_slug)
    return render_to_response("households/household.html", {
        "household": household,
    }, context_instance=RequestContext(request))
    
@login_required
def households(request):
    orgs = Household.objects.all()
    return render_to_response("households/households.html", {
        "households": orgs,
    }, context_instance=RequestContext(request))
