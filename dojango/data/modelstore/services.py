import sys, inspect
from django.utils import simplejson
from exceptions import ServiceException

def servicemethod(*args, **kwargs):
    """ The Service method decorator.

        Decorate a function or method to expose it remotely
        via RPC (or other mechanism.)

        Arguments:

            name (optional):
                The name of this method as seen remotely.

            store (required if not decorating a bound Store method):
                A reference to the Store this method operates on.

                This is required if the method is a regular function,
                a staticmethod or otherwise defined outside a Store instance.
                (ie doesn't take a 'self' argument)

            store_arg (optional):
                Specifies whether this method should be passed the Store instance
                as the first argument (default is True so that servicemethods bound to
                a store instance can get a proper 'self' reference.)

            request_arg (optional):
                Specifies whether this method should be passed a reference to the current
                Request object.  (Default is True)

            If both store_arg and request_arg are True, the the store will be passed first,
            then the request (to appease bound store methods that need a 'self' as the first arg)

            If only one is True then that one will be passed first.  This is useful for using
            standard Django view functions as servicemethods since they require the 'request'
            as the first argument.
    """
    # Default options
    options = {'name': None, 'store': None, 'request_arg': True, 'store_arg': True}

    # Figure out if we were called with arguments
    # If we were called with args, ie:
    # @servicemethod(name='Foo')
    # Then the only argument here will be the pre-decorated function/method object.
    method = ( (len(args) == 1) and callable(args[0]) ) and args[0] or None

    if method is None:
        # We were called with args, (or  @servicemethod() )
        # so figure out what they were ...

        # The method name should be either the first non-kwarg
        # or the kwarg 'name'
        # Example: @servicemethod('my_method', ...) or @servicemethod(name='my_method')
        options.update({
            'name': bool(args) and args[0] or kwargs.pop('name', None),
            'store': (len(args) >= 2) and args[1] or kwargs.pop('store', None),
            'request_arg': kwargs.pop('request_arg', True),
            'store_arg': kwargs.pop('store_arg', True),
        })
    else:
        options['name'] = method.__name__
        method.__servicemethod__ = options

    def method_with_args_wrapper(method):
        """ Wrapper for a method decorated with decorator arguments
        """
        if options['name'] is None:
            options['name'] = method.__name__
        method.__servicemethod__ = options

        if options['store'] is not None:
            options['store'].service.add_method(method)

        return method

    return method or method_with_args_wrapper

class BaseService(object):
    """ The base Service class that manages servicemethods and
        service method descriptions
    """
    def __init__(self):
        """ BaseService constructor
        """
        self.methods = {}
        self._store = None

    def _get_store(self):
        """ Property getter for the store this service is
            bound to
        """
        return self._store

    def _set_store(self, store):
        """ Property setter for the store this service is
            bound to.  Automatically updates the store
            reference in all the __servicemethod__
            properties on servicemethods in this service
        """
        for method in self.methods.values():
            method.__servicemethod__['store'] = store
        self._store = store
    store = property(_get_store, _set_store)

    def _get_method_args(self, method, request, params):
        """ Decide if we should pass store_arg and/or request_arg
            to the servicemethod
        """
        idx = 0

        if method.__servicemethod__['store_arg']:
            params.insert(idx, method.__servicemethod__['store'])
            idx += 1

        if method.__servicemethod__['request_arg']:
            params.insert(idx, request)

        return params

    def add_method(self, method, name=None, request_arg=True, store_arg=True):
        """ Adds a method as a servicemethod to this service.
        """
        # Was this a decorated servicemethod?
        if hasattr(method, '__servicemethod__'):
            options = method.__servicemethod__
        else:
            options = {'name': name or method.__name__, 'store': self.store,
                'request_arg': request_arg, 'store_arg': store_arg}

        method.__servicemethod__ = options
        self.methods[ options['name'] ] = method

    def get_method(self, name):
        """ Returns the servicemethod given by name
        """
        try:
            return self.methods[name]
        except KeyError:
            raise ServiceException('Service method "%s" not registered' % name)

    def list_methods(self):
        """ Returns a list of all servicemethod names
        """
        return self.methods.keys()

    def process_request(self, request):
        """ Processes a request object --

            This is generally the entry point for all
            servicemethod calls
        """
        raise NotImplementedError('process_request not implemented in BaseService')

    def process_response(self, id, result):
        """ Prepares a response from a servicemethod call
        """
        raise NotImplementedError('process_response not implemented in BaseService')

    def process_error(self, id, code, error):
        """ Prepares an error response from a servicemethod call
        """
        raise NotImplementedError('process_error not implemented in BaseService')

    def get_smd(self, url):
        """ Returns a service method description of all public servicemethods
        """
        raise NotImplementedError('get_smd not implemented in BaseService')

class JsonService(BaseService):
    """ Implements a JSON-RPC version 1.1 service
    """

    def __call__(self, request):
        """ JSON-RPC method calls come in as POSTs
            --
            Requests for the SMD come in as GETs
        """

        if request.method == 'POST':
            response = self.process_request(request)

        else:
            response = self.get_smd(request.get_full_path())

        return simplejson.dumps(response)

    def process_request(self, request):
        """ Handle the request
        """
        try:
            data = simplejson.loads(request.raw_post_data)
            id, method_name, params = data["id"], data["method"], data["params"]

        # Doing a blanket except here because God knows kind of crazy
        # POST data might come in.
        except:
            return self.process_error(0, 100, 'Invalid JSON-RPC request')

        try:
            method = self.get_method(method_name)
        except ServiceException:
            return self.process_error(id, 100, 'Unknown method: "%s"' % method_name)

        params = self._get_method_args(method, request, params)

        try:
            result = method(*params)
            return self.process_response(id, result)

        except BaseException:
            etype, eval, etb = sys.exc_info()
            return self.process_error(id, 100, '%s: %s' % (etype.__name__, eval) )

        except:
            etype, eval, etb = sys.exc_info()
            return self.process_error(id, 100, 'Exception %s: %s' % (etype, eval) )

    def process_response(self, id, result):
        """ Build a JSON-RPC 1.1 response dict
        """
        return {
            'version': '1.1',
            'id': id,
            'result': result,
            'error': None,
        }

    def process_error(self, id, code, error):
        """ Build a JSON-RPC 1.1 error dict
        """
        return {
            'id': id,
            'version': '1.1',
            'error': {
                'name': 'JSONRPCError',
                'code': code,
                'message': error,
            },
        }

    def get_smd(self, url):
        """ Generate a JSON-RPC 1.1 Service Method Description (SMD)
        """
        smd = {
            'serviceType': 'JSON-RPC',
            'serviceURL': url,
            'methods': []
        }

        for name, method in self.methods.items():

            # Figure out what params to report --
            # we don't want to report the 'store' and 'request'
            # params to the remote method.
            idx = 0
            idx += method.__servicemethod__['store_arg'] and 1 or 0
            idx += method.__servicemethod__['request_arg'] and 1 or 0

            sig = inspect.getargspec(method)
            smd['methods'].append({
                'name': name,
                'parameters': [ {'name': val} for val in sig.args[idx:] ]
            })

        return smd
