from django.http import HttpResponseServerError

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

    EDIT: I recently changed the request checking to use the is_ajax() method. 
    This gives you access to these simple exceptions for get requests as well 
    (even though you could just point your browser there).
    """
    def process_exception(self, request, exception):
        #if settings.DEBUG:
        if request.META.get('HTTP_X_REQUESTED_WITH', None) == 'XMLHttpRequest':
            import sys, traceback
            (exc_type, exc_info, tb) = sys.exc_info()
            response = "%s\n" % exc_type.__name__
            response += "%s\n\n" % exc_info
            response += "TRACEBACK:\n"    
            for tb in traceback.format_tb(tb):
                response += "%s\n" % tb
            return HttpResponseServerError(response)