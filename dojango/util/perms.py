from django.conf import settings

def access_model(app_name, model_name, request=None, instance=None):
    """
    Return true to allow access to a given instance of app_name.model_name
    """
    acl = getattr(settings, "DOJANGO_DATAGRID_ACCESS", [])
    for x in acl:
        try:
            if x.find(".")>0:
                app,model = x.split('.')
                if app_name == app and model_name==model: return True
            else:
                if app_name == x or model_name==x: return True
        except:
            pass
    return False

def access_model_field(app_name, model_name, field_name, request=None, instance=None):
    """
    Return true to allow access of a given field_name to model app_name.model_name given
    a specific object of said model.
    """
    # in django version 1.2 a new attribute is on all models: _state of type ModelState
    # that field shouldn't be accessible
    return not field_name in ('delete', '_state',)