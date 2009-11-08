from django.utils.datastructures import SortedDict
from django.db.models import get_model
from fields import StoreField
from exceptions import StoreException

def get_object_from_identifier(identifier, valid=None):
    """ Helper function to resolve an item identifier
        into a model instance.

        Raises StoreException if the identifier is invalid
        or the requested Model could not be found

        Raises <Model>.DoesNotExist if the object lookup fails

        Arguments (optional):

            valid
                One or more Django model classes to compare the
                returned model instance to.
    """
    try:
        model_str, pk = identifier.split('__')
    except ValueError:
        raise StoreException('Invalid identifier string')

    Model = get_model(*model_str.split('.'))
    if Model is None:
        raise StoreException('Model from identifier string "%s" not found' % model_str)

    if valid is not None:
        if not isinstance(valid, (list, tuple) ):
            valid = (valid,)
        if Model not in valid:
            raise StoreException('Model type mismatch')

    # This will raise Model.DoesNotExist if lookup fails
    return Model._default_manager.get(pk=pk)

def get_fields_and_servicemethods(bases, attrs, include_bases=True):
    """ This function was pilfered (and slightly modified) from django/forms/forms.py
        See the original function for doc and comments.
    """
    fields = [ (field_name, attrs.pop(field_name)) for \
        field_name, obj in attrs.items() if isinstance(obj, StoreField)]

    # Get the method name directly from the __servicemethod__ dict
    # as set by the decorator
    methods = [ (method.__servicemethod__['name'], method) for \
        method in attrs.values() if hasattr(method, '__servicemethod__') ]

    if include_bases:
        for base in bases[::-1]:

            # Grab the fields and servicemethods from the base classes
            try:
                fields = base.fields.items() + fields
            except AttributeError:
                pass

            try:
                methods = base.servicemethods.items() + methods
            except AttributeError:
                pass

    return SortedDict(fields), SortedDict(methods)

def resolve_dotted_attribute(obj, attr, allow_dotted_names=True):
    """ resolve_dotted_attribute(a, 'b.c.d') => a.b.c.d

        Resolves a dotted attribute name to an object.  Raises
        an AttributeError if any attribute in the chain starts with a '_'

        Modification Note:
        (unless it's the special '__unicode__' method)

        If the optional allow_dotted_names argument is False, dots are not
        supported and this function operates similar to getattr(obj, attr).

        NOTE:
        This method was (mostly) copied straight over from SimpleXMLRPCServer.py in the
        standard library
    """
    if allow_dotted_names:
        attrs = attr.split('.')
    else:
        attrs = [attr]

    for i in attrs:
        if i.startswith('_') and i != '__unicode__': # Allow the __unicode__ method to be called
            raise AttributeError(
                'attempt to access private attribute "%s"' % i
                )
        else:
            obj = getattr(obj,i)
    return obj
