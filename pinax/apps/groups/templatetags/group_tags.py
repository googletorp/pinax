from django import template
from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse, NoReverseMatch


register = template.Library()


class GroupURLNode(template.Node):
    def __init__(self, view_name, group, kwargs, asvar):
        self.view_name = view_name
        self.group = group
        self.kwargs = kwargs
        self.asvar = asvar
    
    def render(self, context):
        url = ""
        group = self.group.resolve(context)
        
        kwargs = {}
        for k, v in self.kwargs.items():
            kwargs[smart_str(k, "ascii")] = v.resolve(context)
        
        if group:
            bridge = group.content_bridge
            try:
                url = bridge.reverse(self.view_name, group, kwargs=kwargs)
            except NoReverseMatch:
                if self.asvar is None:
                    raise
        else:
            try:
                url = reverse(self.view_name, kwargs=kwargs)
            except NoReverseMatch:
                if self.asvar is None:
                    raise
                
        if self.asvar:
            context[self.asvar] = url
            return ""
        else:
            return url


@register.tag
def groupurl(parser, token):
    bits = token.contents.split()
    tag_name = bits[0]
    if len(bits) < 3:
        raise template.TemplateSyntaxError("'%s' takes at least two arguments"
            " (path to a view and a group)" % tag_name)
    
    view_name = bits[1]
    group = parser.compile_filter(bits[2])
    args = []
    kwargs = {}
    asvar = None
    
    if len(bits) > 3:
        bits = iter(bits[3:])
        for bit in bits:
            if bit == "as":
                asvar = bits.next()
                break
            else:
                for arg in bit.split(","):
                    if "=" in arg:
                        k, v = arg.split("=", 1)
                        k = k.strip()
                        kwargs[k] = parser.compile_filter(v)
                    elif arg:
                        raise template.TemplateSyntaxError("'%s' does not support non-kwargs arguments." % tag_name)
    
    return GroupURLNode(view_name, group, kwargs, asvar)
