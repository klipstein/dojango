from django.http import HttpResponseNotAllowed, HttpResponseServerError
from django.utils import simplejson as json

from util import to_json_response
from util import to_dojo_data

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps  # Python 2.3, 2.4 fallback.

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
            return HttpResponseNotAllowed(['POST'])
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
    A simple json response decorator. Use it on views, where a python data object should be converted
    to a json response:

        @json_response
        def my_view(request):
           my_data = {'foo': 'bar'}
           return my_data
    """
    def inner(request, *args, **kwargs):
        ret = func(request, *args, **kwargs)
        return __prepare_json_ret(request, ret)
    return wraps(func)(inner)

def jsonp_response_custom(callback_param_name):
    """
    A jsonp (JSON with Padding) response decorator, where you can define your own callbackParamName.
    It acts like the json_response decorator but with the difference, that it
    wraps the returned json string into a client-specified function name (that is the Padding).
    
    You can add this decorator to a function like that:
    
        @jsonp_response_custom("my_callback_param")
        def my_view(request):
            my_data = {'foo': 'bar'}
            return my_data

    Your now can access this view from a foreign URL using JSONP.
    An example with Dojo looks like that:
    
        dojo.io.script.get({ url:"http://example.com/my_url/",
                             callbackParamName:"my_callback_param",
                             load: function(response){
                                 console.log(response);
                             }
                           });
                           
    Note: the callback_param_name in the decorator and in your JavaScript JSONP call must be the same.
    """
    def decorator(func):
        def inner(request, *args, **kwargs):
            ret = func(request, *args, **kwargs)
            return __prepare_json_ret(request, ret, callback_param_name=callback_param_name)
        return wraps(func)(inner)
    return decorator

jsonp_response = jsonp_response_custom("jsonp_callback")
jsonp_response.__doc__ = "A predefined jsonp response decorator using 'jsoncallback' as a fixed callback_param_name."

def json_iframe_response(func):
    """
    A simple json response decorator but wrapping the json response into a html page.
    It helps when doing a json request using an iframe (e.g. file up-/download):

        @json_iframe
        def my_view(request):
           my_data = {'foo': 'bar'}
           return my_data
    """
    def inner(request, *args, **kwargs):
        ret = func(request, *args, **kwargs)
        return __prepare_json_ret(request, ret, use_iframe=True)
    return wraps(func)(inner)

def __prepare_json_ret(request, ret, callback_param_name=None, use_iframe=False):
    if ret==False:
        ret = {'success':False}
    elif ret==None: # Sometimes there is no return.
        ret = {}
    # Add the 'ret'=True, since it was obviously no set yet and we got valid data, no exception.
    func_name = None
    if callback_param_name:
        func_name = request.GET.get(callback_param_name, "callbackParamName")
    try:
        if not ret.has_key('success'):
            ret['success'] = True
    except AttributeError, e:
        raise Exception("The returned data of your function must be a dictionary!")
    json_ret = ""
    try:
        # Sometimes the serialization fails, i.e. when there are too deeply nested objects or even classes inside
        json_ret = to_json_response(ret, func_name, use_iframe)
    except Exception, e:
        print '\n\n===============Exception=============\n\n'+str(e)+'\n\n' 
        print ret
        print '\n\n'
        return HttpResponseServerError(content=str(e))
    return json_ret
