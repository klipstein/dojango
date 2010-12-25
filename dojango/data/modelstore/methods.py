import utils
from exceptions import MethodException

class Arg(object):
    """ The base placeholder argument class

        There is no reason to use this class directly and really
        only exists to do some type checking on classes that
        inherit from it
    """
    pass

class RequestArg(Arg):
    """ Placeholder argument that represents the current
        Request object.
    """
    pass

class ModelArg(Arg):
    """ Placeholder argument that represents the current
        Model object.

        >>> user = User.objects.get(pk=1)
        >>>

            In this case 'user' is the ObjectArg and
            and 'User' is the ModelArg.
    """
    pass

class ObjectArg(Arg):
    """ Placeholder argument that represents the current
        Model object instance.

        user = User.objects.get(pk=1)

        'user' is the ObjectArg, 'User' is the ModelArg
    """
    pass

class StoreArg(Arg):
    """ Placeholder argument that represents the current
        Store instance.
    """
    pass

class FieldArg(Arg):
    """ Placeholder argument that represents the current
        Field instance.

        This is the field specified on the Store object,
        not the Model object.
    """
    pass


class BaseMethod(object):
    """ The base class from which all proxied methods
        derive.
    """

    def __init__(self, method_or_methodname, *args, **kwargs):
        """ The first argument is either the name of a method
            or the method object itself (ie, pointer to the method)

            The remaining arguments are passed to the given method
            substituting any proxied arguments as needed.

            Usage:
                >>> method = Method('my_method', RequestArg, ObjectArg, 'my other arg', my_kwarg='Something')
                >>> method()
                'My Result'
                >>>

                The method call looks like:
                >>> my_method(request, model_instance, 'my_other_arg', my_kwarg='Something')
        """

        self.method_or_methodname = method_or_methodname
        self.args = args
        self.kwargs = kwargs
        self.field = None # Don't have a handle on the field yet

    def __call__(self):
        """ Builds the arguments and returns the value of the method call
        """

        self._build_args()
        return self.get_value()

    def _build_args(self):
        """ Builds the arguments to be passed to the given method

            Substitutes placeholder args (ie RequestArg, ObjectArg etc.)
            with the actual objects.
        """

        args = []
        for arg in self.args:
            try:
                arg = self.field.proxied_args.get(arg.__name__, arg)
            except AttributeError: # No __name__ attr on the arg
                pass
            args.append(arg)
        self.args = args

        for key, val in self.kwargs.items():
            self.kwargs.update({
                key: self.field.proxied_args.get(hasattr(val, '__name__') and val.__name__ or val, val)
            })

    def get_value(self):
        """ Calls the given method with the requested arguments.
        """
        raise NotImplementedError('get_value() not implemented in BaseMethod')

    def get_method(self, obj=None):
        """ Resolves the given method into a callable object.

            If 'obj' is provided, the method will be looked for as an
            attribute of the 'obj'

            Supports dotted names.

            Usage:
                >>> method = Method('obj.obj.method', RequestArg)
                >>> method()
                'Result of method called with: obj.obj.method(request)'
                >>>

                Dotted attributes are most useful when using something like an
                an ObjectMethod:

                (where 'user' is an instance of Django's 'User' model,
                    the Object in this example is the 'user' instance)

                >>> method = ObjectMethod('date_joined.strftime', '%Y-%m-%d %H:%M:%S')
                >>> method()
                2009-10-02 09:58:39
                >>>

                The actual method call looks like:
                >>> user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
                2009-10-02 09:58:39
                >>>

                It also supports attributes which are not actually methods:

                >>> method = ObjectMethod('first_name', 'ignored arguments', ...) # Arguments to a non-callable are ignored.
                >>> method()
                u'Bilbo'
                >>> method = ValueMethod('first_name', 'upper') # Called on the returned value
                >>> method()
                u'BILBO'
                >>>

                The method call for the last one looks like:
                >>> user.first_name.upper()
                u'BILBO'
                >>>

        """

        if callable(self.method_or_methodname):
            return self.method_or_methodname

        if not isinstance(self.method_or_methodname, (str, unicode) ):
            raise MethodException('Method must a string or callable')

        if obj is not None:

            try:
                method = utils.resolve_dotted_attribute(obj, self.method_or_methodname)
            except AttributeError:
                raise MethodException('Cannot resolve method "%s" in object "%s"' % (
                    self.method_or_methodname, type(obj)
                ))

            if not callable(method):

                # Turn this into a callable
                m = method
                def _m(*args, **kwargs): return m
                method = _m

            return method

        try:
            return eval(self.method_or_methodname) # Just try to get it in current scope
        except NameError:
            raise MethodException('Cannot resolve method "%s"' % self.method_or_methodname)

class Method(BaseMethod):
    """ Basic method proxy class.

        Usage:

            >>> method = Method('my_global_method')
            >>> result = method()

            >>> method = Method(my_method, RequestArg, ObjectArg)
            >>> result = method()

            The real method call would look like:
            >>> my_method(request, model_object)

        Notes:

            If the method passed is the string name of a method,
            it is evaluated in the global scope to get the actual
            method, or MethodException is raised.

            >>> method = Method('my_method')

                Under the hood:
                    >>> try:
                    >>>     method = eval('my_method')
                    >>> except NameError:
                    >>>     ...

    """
    def get_value(self):
        return self.get_method()(*self.args, **self.kwargs)

class ModelMethod(BaseMethod):
    """ A method proxy that will look for the given method
        as an attribute on the Model.
    """
    def get_value(self):
        obj = self.field.proxied_args['ModelArg']
        return self.get_method(obj)(*self.args, **self.kwargs)

class ObjectMethod(BaseMethod):
    """ A method proxy that will look for the given method
        as an attribute on the Model instance.

        Example:

            >>> method = ObjectMethod('get_full_name')
            >>> method()
            u'Bilbo Baggins'

            Assuming this is used on an instance of Django's 'User' model,
            the method call looks like:
            >>> user.get_full_name()

    """
    def get_value(self):
        obj = self.field.proxied_args['ObjectArg']
        return self.get_method(obj)(*self.args, **self.kwargs)

class StoreMethod(BaseMethod):
    """ A method proxy that will look for the given method
        as an attribute on the Store.
    """
    def get_value(self):
        obj = self.field.proxied_args['StoreArg']
        return self.get_method(obj)(*self.args, **self.kwargs)

class FieldMethod(BaseMethod):
    """ A method proxy that will look for the given method
        as an attribute on the Field.

        Notes:
            Field is the field on the Store, not the Model.
    """
    def get_value(self):
        obj = self.field.proxied_args['FieldArg']
        return self.get_method(obj)(*self.args, **self.kwargs)

class ValueMethod(BaseMethod):
    """ A method proxy that will look for the given method
        as an attribute on the value of a field.

        Usage:
            >>> user = User.objects.get(pk=1)
            >>> user.date_joined
            datetime.datetime(..)
            >>>

            A ValueMethod would look for the given method on
            the datetime object:

            >>> method = ValueMethod('strftime', '%Y-%m-%d %H:%M:%S')
            >>> method()
            u'2009-10-02 12:32:12'
            >>>
    """
    def get_value(self):
        obj = self.field.proxied_args['ObjectArg']
        val = utils.resolve_dotted_attribute(obj, self.field.model_field_name)

        # Prevent throwing a MethodException if the value is None
        if val is None:
            return None
        return self.get_method(val)(*self.args, **self.kwargs)

###
# Pre-built custom Methods
###
DojoDateMethod = ValueMethod('strftime', '%Y-%m-%dT%H:%M:%S')
