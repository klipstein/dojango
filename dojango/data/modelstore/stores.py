from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.core.paginator import Paginator

from utils import get_fields_and_servicemethods
from exceptions import StoreException, ServiceException
from services import JsonService, servicemethod

__all__ = ('Store', 'ModelQueryStore')

class StoreMetaclass(type):
    """ This class (mostly) came from django/forms/forms.py
        See the original class 'DeclarativeFieldsMetaclass' for doc and comments.
    """
    def __new__(cls, name, bases, attrs):

        # Get the declared StoreFields and service methods
        fields, servicemethods = get_fields_and_servicemethods(bases, attrs)

        attrs['servicemethods'] = servicemethods

        # Tell each field the name of the attribute used to reference it
        # in the Store
        for fieldname, field in fields.items():
            setattr(field, '_store_attr_name', fieldname)
        attrs['fields'] = fields

        return super(StoreMetaclass, cls).__new__(cls, name, bases, attrs)

class BaseStore(object):
    """ The base Store from which all Stores derive
    """

    class Meta(object):
        """ Inner class to hold store options.

            Same basic concept as Django's Meta class
            on Model definitions.
        """
        pass

    def __init__(self, objects=None, stores=None, identifier=None, label=None, is_nested=False):
        """ Store instance constructor.

            Arguments (all optional):

                objects:
                    The list (or any iterable, ie QuerySet) of objects that will
                    fill the store.

                stores:
                    One or more Store objects to combine together into a single
                    store.  Useful when using ReferenceFields to build a store
                    with objects of more than one 'type' (like Django models
                    via ForeignKeys, ManyToManyFields etc.)

                identifier:
                    The 'identifier' attribute used in the store.

                label:
                    The 'label' attribute used in the store.
                
                is_nested:
                    This is required, if we want to return the items as direct
                    array and not as dictionary including 
                    {'identifier': "id", 'label', ...}
                    It mainly is required, if children of a tree structure needs
                    to be rendered (see TreeStore).
        """

        # Instantiate the inner Meta class
        self._meta = self.Meta()

        # Move the fields into the _meta instance
        self.set_option('fields', self.fields)

        # Set the identifier
        if identifier:
            self.set_option('identifier', identifier)
        elif not self.has_option('identifier'):
            self.set_option('identifier', 'id')

        # Set the label
        if label:
            self.set_option('label', label)
        elif not self.has_option('label'):
            self.set_option('label', 'label')
        
        # Is this a nested store? (indicating that it should be rendered as array)
        self.is_nested = is_nested

        # Set the objects
        if objects != None:
            self.set_option('objects', objects)
        elif not self.has_option('objects'):
            self.set_option('objects', [])

        # Set the stores
        if stores:
            self.set_option('stores', stores)
        elif not self.has_option('stores'):
            self.set_option('stores', [])

        # Instantiate the stores (if required)
        self.set_option('stores', [ isinstance(s, Store) and s or s() for s in self.get_option('stores') ])

        # Do we have service set?
        try:
            self.service = self.get_option('service')
            self.service.store = self

            # Populate all the declared servicemethods
            for method in self.servicemethods.values():
                self.service.add_method(method)

        except StoreException:
            self.service = None

        self.request = None # Placeholder for the Request object (if used)
        self.data = self.is_nested and [] or {} # The serialized data in it's final form

    def has_option(self, option):
        """ True/False whether the given option is set in the store
        """
        try:
            self.get_option(option)
        except StoreException:
            return False
        return True

    def get_option(self, option):
        """ Returns the given store option.
            Raises a StoreException if the option isn't set.
        """
        try:
            return getattr(self._meta, option)
        except AttributeError:
            raise StoreException('Option "%s" not set in store' % option)

    def set_option(self, option, value):
        """ Sets a store option.
        """
        setattr(self._meta, option, value)

    def __call__(self, request):
        """ Called when an instance of this store is called
            (ie as a Django 'view' function from a URLConf).

            It accepts the Request object as it's only param, which
            it makes available to other methods at 'self.request'.

            Returns the serialized store as Json.
        """
        self.request = request

        if self.service:
            self._merge_servicemethods()
            if not self.is_nested:
                self.data['SMD'] = self.service.get_smd( request.get_full_path() )

            if request.method == 'POST':
                return self.service(request)

        return self.to_json()

    def __str__(self):
        """ Renders the store as Json.
        """
        return self.to_json()

    def __repr__(self):
        """ Renders the store as Json.
        """
        count = getattr(self.get_option('objects'), 'count', '__len__')()
        return '<%s: identifier: %s, label: %s, objects: %d>' % (
            self.__class__.__name__, self.get_option('identifier'), self.get_option('label'), count)

    def get_identifier(self, obj):
        """ Returns a (theoretically) unique key for a given
            object of the form: <appname>.<modelname>__<pk>
        """
        return smart_unicode('%s__%s' % (
            obj._meta,
            obj._get_pk_val(),
        ), strings_only=True)

    def get_label(self, obj):
        """ Calls the object's __unicode__ method
            to get the label if available or just returns
            the identifier.
        """
        try:
            return obj.__unicode__()
        except AttributeError:
            return self.get_identifier(obj)

    def _merge_servicemethods(self):
        """ Merges the declared service methods from multiple
            stores into a single store.  The store reference on each
            method will still point to the original store.
        """
        # only run if we have a service set
        if self.service:

            for store in self.get_option('stores'):
                if not store.service: # Ignore when no service is defined.
                    continue

                for name, method in store.service.methods.items():
                    try:
                        self.service.get_method(name)
                        raise StoreException('Combined stores have conflicting service method name "%s"' % name)
                    except ServiceException: # This is what we want

                        # Don't use service.add_method since we want the 'foreign' method to
                        # stay attached to the original store
                        self.service.methods[name] = method

    def _merge_stores(self):
        """ Merge all the stores into one.
        """
        for store in self.get_option('stores'):

            # The other stores will (temporarily) take on this store's 'identifier' and
            # 'label' settings
            orig_identifier = store.get_option('identifier')
            orig_label = store.get_option('label')
            for attr in ('identifier', 'label'):
                store.set_option(attr, self.get_option(attr))

            self.data['items'] += store.to_python()['items']

            # Reset the old values for label and identifier
            store.set_option('identifier', orig_identifier)
            store.set_option('label', orig_label)

    def add_store(self, *stores):
        """ Add one or more stores to this store.

            Arguments (required):

                stores:
                    One or many Stores (or Store instances) to add to this store.

            Usage:

                >>> store.add_store(MyStore1, MyStore2(), ...)
                >>>
        """
        # If a non-instance Store is given, instantiate it.
        stores = [ isinstance(s, Store) and s or s() for s in stores ]
        self.set_option('stores', list( self.get_option('stores') ) + stores )

    def to_python(self, objects=None):
        """ Serialize the store into a Python dictionary.

            Arguments (optional):

                objects:
                    The list (or any iterable, ie QuerySet) of objects that will
                    fill the store -- the previous 'objects' setting will be restored
                    after serialization is finished.
        """

        if objects is not None:
            # Save the previous objects setting
            old_objects = self.get_option('objects')
            self.set_option('objects', objects)
            self._serialize()
            self.set_option('objects', old_objects)
        else:
            self._serialize()

        return self.data

    def to_json(self, *args, **kwargs):
        """ Serialize the store as Json.

            Arguments (all optional):

                objects:
                    (The kwarg 'objects')
                    The list (or any iterable, ie QuerySet) of objects that will
                    fill the store.

                All other args and kwargs are passed to simplejson.dumps
        """
        objects = kwargs.pop('objects', None)
        return simplejson.dumps( self.to_python(objects), *args, **kwargs )

    def _start_serialization(self):
        """ Called when serialization of the store begins
        """
        if not self.is_nested:
            self.data['identifier'] = self.get_option('identifier')

        # Don't set a label field in the store if it's not wanted
        if bool( self.get_option('label') ) and not self.is_nested:
            self.data['label'] = self.get_option('label')

        if self.is_nested:
            self.data = []
        else:
            self.data['items'] = []

    def _start_object(self, obj):
        """ Called when starting to serialize each object in 'objects'

            Requires an object as the only argument.
        """
        # The current object in it's serialized state.
        self._item = {self.get_option('identifier'): self.get_identifier(obj)}

        label = self.get_option('label')

        # Do we have a 'label' and is it already the
        # name of one of the declared fields?
        if label and ( label not in self.get_option('fields').keys() ):

            # Have we defined a 'get_label' method on the store?
            if callable( getattr(self, 'get_label', None) ):
                self._item[label] = self.get_label(obj)

    def _handle_field(self, obj, field):
        """ Handle the given field in the Store
        """
        # Fill the proxied_args on the field (for get_value methods that use them)
        field.proxied_args.update({
            'RequestArg': self.request,
            'ObjectArg': obj,
            'ModelArg': obj.__class__,
            'FieldArg': field,
            'StoreArg': self,
        })

        # Get the value
        self._item[field.store_field_name] = field.get_value()

    def _end_object(self, obj):
        """ Called when serializing an object ends.
        """
        if self.is_nested:
            self.data.append(self._item)
        else:
            self.data['items'].append(self._item)
        self._item = None

    def _end_serialization(self):
        """ Called when serialization of the store ends
        """
        pass

    def _serialize(self):
        """ Serialize the defined objects and stores into it's final form
        """
        self._start_serialization()
        for obj in self.get_option('objects'):
            self._start_object(obj)

            for field in self.get_option('fields').values():
                self._handle_field(obj, field)

            self._end_object(obj)
        self._end_serialization()
        self._merge_stores()

class Store(BaseStore):
    """ Just defines the __metaclass__

        All the real functionality is implemented in
        BaseStore
    """
    __metaclass__ = StoreMetaclass

class ModelQueryStore(Store):
    """ A store designed to be used with dojox.data.QueryReadStore

        Handles paging, sorting and filtering

        At the moment it requires a custom subclass of QueryReadStore
        that implements the necessary mechanics to handle server queries
        the the exported Json RPC 'fetch' method.  Soon it will support
        QueryReadStore itself.
    """
    def __init__(self, *args, **kwargs):
        """
        """

        objects_per_query = kwargs.pop('objects_per_query', None)

        super(ModelQueryStore, self).__init__(*args, **kwargs)

        if objects_per_query is not None:
            self.set_option('objects_per_query', objects_per_query)
        elif not self.has_option('objects_per_query'):
            self.set_option('objects_per_query', 25)

    def filter_objects(self, request, objects, query):
        """ Overridable method used to filter the objects
            based on the query dict.
        """
        return objects

    def sort_objects(self, request, objects, sort_attr, descending):
        """ Overridable method used to sort the objects based
            on the attribute given by sort_attr
        """
        return objects

    def __call__(self, request):
        """
        """
        self.request = request

        # We need the request.GET QueryDict to be mutable.
        query_dict = {}
        for k,v in request.GET.items():
            query_dict[k] = v

        # dojox.data.QueryReadStore only handles sorting by a single field
        sort_attr   = query_dict.pop('sort', None)
        descending  = False
        if sort_attr and sort_attr.startswith('-'):
            descending = True
            sort_attr = sort_attr.lstrip('-')

        # Paginator is 1-indexed
        start_index = int( query_dict.pop('start', 0) ) + 1

        # Calculate the count taking objects_per_query into account
        objects_per_query = self.get_option('objects_per_query')
        count = query_dict.pop('count', objects_per_query)

        # We don't want the client to be able to ask for a million records.
        # They can ask for less, but not more ...
        if count == 'Infinity' or int(count) > objects_per_query:
            count = objects_per_query
        else:
            count = int(count)

        objects = self.filter_objects(request, self.get_option('objects'), query_dict)
        objects = self.sort_objects(request, objects, sort_attr, descending)

        paginator = Paginator(objects, count)

        page_num = 1
        for i in xrange(1, paginator.num_pages + 1):
            if paginator.page(i).start_index() <= start_index <= paginator.page(i).end_index():
                page_num = i
                break

        page = paginator.page(page_num)

        data = self.to_python(objects=page.object_list)
        data['numRows'] = paginator.count
        return data
