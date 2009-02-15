from django import template

register = template.Library()

def attachments(context, obj):
    return {
        'object': obj, 
        'request': context['request'],
        'user': context['user'],
        'is_officer': context['is_officer'],
    }

register.inclusion_tag('attachments/attachments.html', takes_context=True)(attachments)
