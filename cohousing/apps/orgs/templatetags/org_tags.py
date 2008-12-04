from django.template import Library, Variable, TemplateSyntaxError, Node
from django.conf import settings
from django.utils.encoding import force_unicode, iri_to_uri
from django.utils.safestring import mark_safe, SafeData

register = Library()

from django.core.urlresolvers import reverse, NoReverseMatch

register = Library()


# based on http://www.djangosnippets.org/snippets/475/
class RelatedNode(Node):
    def __init__(self, object_list, viewname):
        self.object_list = Variable(object_list)
        self.viewname = viewname

    def render(self, context):
        def node(object):
            try:
                reversed = reverse(self.viewname, kwargs={"org_slug": object.slug})
            except NoReverseMatch:
                return '<li>%s</li>' % object

            return '<li><a href="%s">%s</li>' % (reversed, object)

        def recursive(object):
            if object.children.all():
                output.append('<ul>')
                for object in object.children.all():
                    output.append(node(object))
                    recursive(object)
                output.append('</ul>')

        output = []
        for object in self.object_list.resolve(context):
            if not object.parent:
                output.append(node(object))
                recursive(object)

        return '\n'.join(output)

def related_linked_list(parser, token):
    bits = token.contents.split()
    if len(bits) != 3:
        raise TemplateSyntaxError, "'%s' tag takes exactly 2 arguments" % bits[0]
    return RelatedNode(bits[1], bits[2])

register.tag(related_linked_list)


def org_outline(value, autoescape=None):
    """
    Recursively takes a self-nested list and returns an HTML unordered list
    of hyperlinks -- WITHOUT opening and closing <ul> tags.
    
    This is a clone and extension of the default unordered_list filter.
    The list must be a nested list of Org instances, not strings.
    
    """
    if autoescape:
        from django.utils.html import conditional_escape
        escaper = conditional_escape
    else:
        escaper = lambda x: x
    def convert_old_style_list(list_):
        """
        Converts old style lists to the new easier to understand format.

        The old list format looked like:
            ['Item 1', [['Item 1.1', []], ['Item 1.2', []]]

        And it is converted to:
            ['Item 1', ['Item 1.1', 'Item 1.2]]
        """
        if not isinstance(list_, (tuple, list)) or len(list_) != 2:
            return list_, False
        first_item, second_item = list_
        if second_item == []:
            return [first_item], True
        old_style_list = True
        new_second_item = []
        for sublist in second_item:
            item, old_style_list = convert_old_style_list(sublist)
            if not old_style_list:
                break
            new_second_item.extend(item)
        if old_style_list:
            second_item = new_second_item
        return [first_item, second_item], old_style_list
    def _helper(list_, tabs=1):
        indent = u'\t' * tabs
        output = []

        list_length = len(list_)
        i = 0
        while i < list_length:
            title = list_[i]
            sublist = ''
            sublist_item = None
            if isinstance(title, (list, tuple)):
                sublist_item = title
                title = ''
            elif i < list_length - 1:
                next_item = list_[i+1]
                if next_item and isinstance(next_item, (list, tuple)):
                    # The next item is a sub-list.
                    sublist_item = next_item
                    # We've processed the next item now too.
                    i += 1
            if sublist_item:
                sublist = _helper(sublist_item, tabs+1)
                sublist = '\n%s<ul>\n%s\n%s</ul>\n%s' % (indent, sublist,
                                                         indent, indent)
            hyperlink = "<a href='%s'>%s</a>" % (title.get_absolute_url(),
                                                 title.name)
            output.append('%s<li>%s%s</li>' % (indent,
                    escaper(force_unicode(hyperlink)), sublist))
            i += 1
        return '\n'.join(output)
    value, converted = convert_old_style_list(value)
    return mark_safe(_helper(value))
org_outline.is_safe = True
org_outline.needs_autoescape = True

register.filter(org_outline)

def show_task(task):
    return {"task": task}
register.inclusion_tag("orgs/task_item.html")(show_task)

def show_aim(aim):
    return {"aim": aim}
register.inclusion_tag("orgs/aim_item.html")(show_aim)

def show_meeting_topic(topic):
    return {"topic": topic}
register.inclusion_tag("orgs/topic_item.html")(show_meeting_topic)
