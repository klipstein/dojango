from django import template

from dojango.conf import settings # using the app-specific settings
from dojango.util import json_encode as util_json_encode
from dojango.util.config import Config

register = template.Library()

class DojangoParamsNode(template.Node):
    '''We set the DOJANGO context with this node!'''
    def __init__(self, profile=settings.DOJO_PROFILE, version=settings.DOJO_VERSION):
        self.profile = profile
        self.version = version
    def render(self, context):
        config = Config(self.profile, self.version)
        if not config.config:
            raise template.TemplateSyntaxError, "Could not find the profile '%s' in the DOJANGO_DOJO_PROFILES settings" % (self.profile)
        if not config.dojo_base_url:
            raise template.TemplateSyntaxError, "The version %s is not supported by the dojango profile '%s'" % (self.version, self.profile)
        context['DOJANGO'] = config.get_context_dict()
        return ''
        
@register.tag
def set_dojango_context(parser, token):
    '''Sets the DOJANGO context constant in the context.
    It is also possible to set the used profile/version with it, e.g.:
      {% set_dojango_context "google" "1.1.1" %}'''
    tlist = token.split_contents()
    # the profile was passed
    if len(tlist) == 2:
        return DojangoParamsNode(tlist[1][1:-1])
    if len(tlist) == 3:
        return DojangoParamsNode(tlist[1][1:-1], tlist[2][1:-1])
    return DojangoParamsNode()

# TODO: Implement template-tag for layout components to register e.g. dojoType="dijit.layout.TabContainer"
# {% dojo_type "dijit.layout.TabContainer" %}
# This template tag informs the collector about new modules

