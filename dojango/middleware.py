import re

from django.conf import settings
from django.http import HttpResponseServerError
from django.utils.encoding import smart_unicode

from dojango.util import dojo_collector

class AJAXSimpleExceptionResponse:
    """Thanks to newmaniese of http://www.djangosnippets.org/snippets/650/ .

    Full doc (copied from link above).
    When debugging AJAX with Firebug, if a response is 500, it is a
    pain to have to view the entire source of the pretty exception page.
    This is a simple middleware that just returns the exception without
    any markup. You can add this anywhere in your python path and then
    put it in you settings file. It will only unprettify your exceptions
    when there is a XMLHttpRequest header. Tested in FF2 with the YUI XHR.
    Comments welcome.
    """
    def process_exception(self, request, exception):
        #if settings.DEBUG:
        # we should use that setting in future version of dojango
        #if request.is_ajax(): # new in django version 1.0
        if request.META.get('HTTP_X_REQUESTED_WITH', None) == 'XMLHttpRequest':
            import sys, traceback
            (exc_type, exc_info, tb) = sys.exc_info()
            response = "%s\n" % exc_type.__name__
            response += "%s\n\n" % exc_info
            response += "TRACEBACK:\n"
            for tb in traceback.format_tb(tb):
                response += "%s\n" % tb
            return HttpResponseServerError(response)

class DojoCollector:
    """This middleware enables/disables the global collector object for each 
    request. It is needed, when the dojango.forms integration is used.
    """
    def process_request(self, request):
        dojo_collector.activate()

    def process_response(self, request, response):
        dojo_collector.deactivate()
        return response
    
class DojoAutoRequire:
    """
    USE THE MIDDLEWARE ABOVE (IT IS USING A GLOBAL COLLECTOR OBEJCT)!
    
    This middleware detects all dojoType="*" definitions in the returned
    response and uses that information to generate all needed dojo.require
    statements and places a <script> block in front of the </body> tag.

    It is just processed for text/html documents!
    """
    def process_response(self, request, response):
        # just process html-pages that were returned by a view
        if response and\
           response.get("Content-Type", "") == "text/html; charset=%s" % settings.DEFAULT_CHARSET and\
           len(response.content) > 0: # just for html pages!
            dojo_type_re = re.compile('\sdojoType\s*\=\s*[\'\"]([\w\d\.\-\_]*)[\'\"]\s*')
            unique_dojo_modules = set(dojo_type_re.findall(response.content)) # we just need each module once
            if len(unique_dojo_modules) > 0:
                tail, sep, head = smart_unicode(response.content).rpartition("</body>")
                response.content = "%(tail)s%(script)s%(sep)s%(head)s" % {
                    'tail':tail,
                    'script':'<script type="text/javascript">\n%s\n</script>\n' % self._get_dojo_requires(unique_dojo_modules),
                    'sep':sep,
                    'head':head,
                }
        return response

    def _get_dojo_requires(self, dojo_modules):
        return "\n".join([u"dojo.require(\"%s\");" % require for require in dojo_modules])
