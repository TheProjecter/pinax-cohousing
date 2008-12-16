from django.db.models import signals

from django.utils.translation import ugettext_noop as _

try:
    from notification import models as notification
    
    def create_notice_types(app, created_models, verbosity, **kwargs):        
        notification.create_notice_type("orgs_new_topic", _("New Organization Topic Started"), _("a new topic has started in an organization you're a member of"), default=2)
        notification.create_notice_type("orgs_topic_response", _("Response To Your Organization Topic"), _("someone has responded on an organization topic you started"), default=2)
        
        notification.create_notice_type("orgs_new_task", _("New Organization Task"), _("a new task been created in an organization you're a member of"), default=2)
        notification.create_notice_type("orgs_task_comment", _("Comment on Organization Task"), _("a new comment has been made on a task in an organization you're a member of"), default=2)
        notification.create_notice_type("orgs_task_change", _("Change to Organization Task"), _("there has been a change in the state of a task in an organization you're a member of"), default=2)
        notification.create_notice_type("orgs_task_assignment", _("Change to Organization Task"), _("a task has been (re)assigned in an organization you're a member of"), default=2)
        notification.create_notice_type("orgs_task_status", _("Change to Organization Task"), _("there has been a status update to a task in an organization you're a member of"), default=2)
        notification.create_notice_type("orgs_meeting_announcement", _("Meeting Announcement"), _("a meeting has been announced"), default=2)
        notification.create_notice_type("orgs_meeting_approval", _("Meeting Agenda Approval"), _("a meeting agenda approval has been requested"), default=2)
        
    signals.post_syncdb.connect(create_notice_types, sender=notification)
except ImportError:
    print "Skipping creation of NoticeTypes as notification app not found"
