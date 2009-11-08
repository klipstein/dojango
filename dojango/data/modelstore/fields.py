import utils
from exceptions import FieldException
import methods

__all__ = ('FieldException', 'StoreField'
            'ReferenceField', 'DojoDateField')

class StoreField(object):
    """ The base StoreField from which all ```StoreField```s derive
    """

    def __init__(self, model_field=None, store_field=None, get_value=None, sort_field=None, can_sort=True):
        """ A StoreField corresponding to a field on a model.

            Arguments (all optional):

                model_field
                    The name of the field on the model.  If omitted then
                    it's assumed to be the attribute name given to this StoreField
                    in the Store definition.

                    Example:

                    >>> class MyStore(Store):
                    >>>     field_1 = StoreField() # The model_field will be Model.field_1
                    >>>     field_2 = StoreField('my_field') # The model_field will be Model.my_field

                store_field
                    The name of the field in the final store.  If omitted then
                    it will be the attribute name given to this StoreField in the
                    Store definition.

                    Example:

                    >>> class MyStore(Store):
                    >>>     field_1 = StoreField() # The store_field will be 'field_1'
                    >>>     field_2 = StoreField(store_field='my_store_field')

                get_value
                    An instance of modelstore.methods.BaseMethod (or any callable)
                    used to get the final value from the field (or anywhere) that
                    will go in the store.

                    Example:

                    def get_custom_value():
                        return 'my custom value'

                    >>> class MyStore(Store):
                            # get_custom_value will be called with no arguments
                    >>>     field_1 = StoreField(get_value=get_custom_value) 

                            # Wrap your method in an instance of methods.BaseMethod if you want to pass
                            # custom arguments -- see methods.BaseMethod (and it's derivatives) for full docs.
                    >>>     field_2 = StoreField(get_value=Method(get_custom_value, arg1, arg2, arg3))

                sort_field
                    Denotes the string used with QuerySet.order_by() to sort the objects
                    by this field.

                    Either the value passed to 'order_by()' on Django
                    QuerySets or an instance of modelstore.methods.BaseMethod
                    (or any callable) which returns the value.

                    Requests to sort descending are handled automatically by prepending the sort field
                    with '-'

                    Example:

                    >>> class MyStore(Store):
                            # QuerySet.order_by() will be called like: QuerySet.order_by('my_model_field')
                    >>>     field_1 = StoreField('my_model_field')

                            # Sorting by dotted fields.
                    >>>     field_2 = StoreField('my.dotted.field', sort_field='my__dotted__field')

                can_sort
                    Whether or not this field can be order_by()'d -- Default is True.

                    If this is False, then attempts to sort by this field will be ignored.
        """

        self._model_field_name = model_field
        self._store_field_name = store_field
        self._store_attr_name = None # We don't know this yet
        self.can_sort = can_sort
        self._sort_field = sort_field
        self._get_value = get_value

        # Attach a reference to this field to the get_value method
        # so it can access proxied_args
        if self._get_value:
            setattr(self._get_value, 'field', self)

        # Proxied arguments (ie, RequestArg, ObjectArg etc.)
        self.proxied_args = {}

    def _get_sort_field(self):
        """ Return the name of the field to be passed to
            QuerySet.order_by().

            Either the name of the value passed to 'order_by()' on Django
            QuerySets or some method which returns the value.
        """
        if (self._sort_field is None) or isinstance(self._sort_field, (str, unicode) ):
            return self._sort_field
        else:
            return self._sort_field()
    sort_field = property(_get_sort_field)

    def _get_store_field_name(self):
        """ Return the name of the field in the final store.

            If an explicit store_field is given in the constructor then that is
            used, otherwise it's the attribute name given to this field in the
            Store definition.
        """
        return self._store_field_name or self._store_attr_name
    store_field_name = property(_get_store_field_name)

    def _get_model_field_name(self):
        """ Return the name of the field on the Model that this field
            corresponds to.

            If an explicit model_field (the first arg) is given in the constructor
            then that is used, otherwise it's assumed to be the attribute name
            given to this field in the Store definition.
        """
        return self._model_field_name or self._store_attr_name
    model_field_name = property(_get_model_field_name)

    def get_value(self):
        """ Returns the value for this field
        """
        if not self._get_value:
            self._get_value = methods.ObjectMethod(self.model_field_name)
            self._get_value.field = self

        return self._get_value()

class ReferenceField(StoreField):
    """ A StoreField that handles '_reference' items

        Corresponds to model fields that refer to other models,
        ie, ForeignKey, ManyToManyField etc.
    """

    def get_value(self):
        """ Returns a list (if more than one) or dict
            of the form:

            {'_reference': '<item identifier>'}
        """

        # The Store we're attached to
        store = self.proxied_args['StoreArg']

        items = []

        if not self._get_value:
            self._get_value = methods.ObjectMethod(self.model_field_name)
            self._get_value.field = self

        related = self._get_value()

        if not bool(related):
            return items

        # Is this a model instance (ie from ForeignKey) ?
        if hasattr(related, '_get_pk_val'):
            return {'_reference': store.get_identifier(related)}

        # Django Queryset or Manager
        if hasattr(related, 'iterator'):
            related = related.iterator()

        try:
            for item in related:
                items.append({'_reference': store.get_identifier(item)})
        except TypeError:
            raise FieldException('Cannot iterate on field "%s"' % (
                self.model_field_name
            ))

        return items

###
# Pre-built custom Fields
###

class DojoDateField(StoreField):

    def get_value(self):

        self._get_value = methods.DojoDateMethod
        self._get_value.field = self
        return self._get_value()
