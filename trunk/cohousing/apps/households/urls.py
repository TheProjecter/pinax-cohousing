from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # all households
    url(r'households/$', 'households.views.households', name="households"),
    # a single households
    url(r'household/(?P<household_slug>[-\w]+)/$', 'households.views.household', name="household"),
)
