from stores import Store
from fields import StoreField
from methods import BaseMethod

class ChildrenMethod(BaseMethod):
    """ A method proxy that will resolve the children
        of a model that has a tree structure.
        "django-treebeard" and "django-mptt" both attach a get_children method
        to the model.
    """
    def get_value(self):
        store = self.field.proxied_args['StoreArg']
        obj = self.field.proxied_args['ObjectArg']
        ret = []
        # TODO: optimize using get_descendants()
        if hasattr(obj, "get_children"):
            ret = store.__class__(objects=obj.get_children(), is_nested=True).to_python()
        return ret

class ChildrenField(StoreField):
    """ A field that renders children items
        If your model provides a get_children method you can use that field
        to render all children recursively. 
        (see "django-treebeard", "django-mptt")
    """
    def get_value(self):
        self._get_value = ChildrenMethod(self.model_field_name)
        self._get_value.field = self
        return self._get_value()

class TreeStore(Store):
    """ A store that already includes the children field with no additional
        options. Just subclass that Store, add the to-be-rendered fields and
        attach a django-treebeard (or django-mptt) model to its Meta class:
        
        class MyStore(TreeStore):
            username = StoreField()
            first_name = StoreField()
            
            class Meta:
                objects = YourTreeModel.objects.filter(id=1) # using treebeard or mptt
                label = 'username'
    """
    children = ChildrenField()