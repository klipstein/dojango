from django.http import HttpResponseServerError
from django.utils import simplejson as json

from util import json_response as json_resp
from util import to_dojo_data

def expect_post_request(func):
    """Allow only POST requests to come in, throw an exception otherwise.
    
    This relieves from checking every time that the request is 
    really a POST request, which it should be when using this 
    decorator.
    """
    def _ret(*args, **kwargs):
        ret = func(*args, **kwargs)
        request = args[0]
        if not request.method=='POST':
            raise Exception('POST request expected.')
        return ret
    return _ret

def add_request_getdict(func):
    """Add the method getdict() to the request object.
    
    This works just like getlist() only that it decodes any nested 
    JSON encoded object structure.
    Since sending deep nested structures is not possible via
    GET/POST by default, this enables it. Of course you need to
    make sure that on the JavaScript side you are also sending
    the data properly, which dojango.send() automatically does.
    Example:
        this is being sent:
            one:1
            two:{"three":3, "four":4}
        using
            request.POST.getdict('two')
        returns a dict containing the values sent by the JavaScript.
    """
    def _ret(*args, **kwargs):
        args[0].POST.__class__.getdict = __getdict
        ret = func(*args, **kwargs)
        return ret
    return _ret

def __getdict(self, key):
    ret = self.get(key)
    try:
        ret = json.loads(ret)
    except ValueError: # The value was not JSON encoded :-)
        raise Exception('"%s" was not JSON encoded as expected (%s).' % (key, str(ret)))
    return ret

def json_response(func):
    """
    """
    def _ret(*args, **kwargs):
        ret = func(*args, **kwargs)
        if ret==False:
            ret = {'success':False}
        elif ret==None: # Sometimes there is no return.
            ret = {}
        # Add the 'ret'=True, since it was obviously no set yet and we got valid data, no exception.
        if not ret.has_key('success'):
            ret['success'] = True
        json_ret = ""
        try:
            # Sometimes the serialization fails, i.e. when there are too deeply nested objects or even classes inside
            json_ret = json_resp(ret)
        except Exception, e:
            print '\n\n===============Exception=============\n\n'+str(e)+'\n\n' 
            print ret
            print '\n\n'
            return HttpResponseServerError(content=str(e))
        return json_ret
    return _ret

