from django import template
from django.db.models import get_model
from django.db import models
from django.template import TemplateSyntaxError
from django.template.loader import get_template

from dojango.util import extract_nodelist_options
from dojango.util.dojo_collector import add_module
from dojango.util.perms import access_model
from django.core.urlresolvers import reverse, NoReverseMatch

import random

register = template.Library()
disp_list_guid = 0
 
FIELD_ATTRIBUTES = ('column_width', 'label', 'formatter')

@register.tag
def simple_datagrid(parser, token):
    """
    Generates a dojo datagrid for a given app's model.
    i.e.  {% simple_datagrid myapp mymodel %}
    """
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError, "You have to pass app- and model-name to {% simple_datagrid app model %}"
    return DatagridNode(bits[1],bits[2],None)

@register.tag
def datagrid(parser, token):
    """
     Generates a dojo datagrid for a given app's model. renders
     the contents until {% enddatagrid %} and takes options in
     the form of option=value per line.
    """
    bits = token.split_contents()
    nodelist = parser.parse(('enddatagrid',))
    parser.delete_first_token()
    app, model = None, None
    if len(bits) == 3:
        app = bits[1]
        model = bits[2]
    return DatagridNode(app, model,nodelist)
                 
class DatagridNode(template.Node):
    """
    If nodelist is not None this will render the contents under the templates
    context then render the dojango/templatetag/datagrid_disp.html template
    under a context created by the options parsed out of the block.
    
    Available options:
    
    list_display:      list or tuple of model attributes (model fields or model functions). defaults to all of the sql fields of the model
    column_width:      dict with model attribute:width
    default_width:     default width if not specified by column_width. defaults to "auto"
    width:             width of the datagrid, defaults to "100%"
    height:            height of datagrid, defaults to "100%"
    id:                id of datagird, optional but useful to if planning on using dojo.connect to the grid.
    label:             dict of attribute:label for header. (other ways exist of setting these)
    query:             way to specify conditions for the table. i.e. to only display elements whose id>10: query={ 'id__gt':10 }
    search:            list or tuple of fields to query against when searching
    show_search:       Display search field (default: True). If False, you'll create your custom search field and call do_{{id}}_search 
    nosort:            fields not to sort on
    formatter:         dict of attribute:js formatter function
    json_store_url:    URL for the ReadQueryStore 
    selection_mode:    dojo datagrid selectionMode
    """
    model = None
    app_name = None
    model_name = None

    def __init__(self, app, model, options):
        if app and model:
            self.model = get_model(app,model)
            self.app_name = app
            self.model_name = model
        self.options = options
        
    def render(self, context):
        opts = {}
        global disp_list_guid
        disp_list_guid = disp_list_guid + 1
        # add dojo modules
        add_module("dojox.data.QueryReadStore")
        add_module("dojox.grid.DataGrid")
        
        # Setable options, not listed: label, query, search, nosort
        if self.model:
            opts['list_display'] = [x.attname for x in self.model._meta.fields]
        opts['width'] = {}
        opts['label'] = {}
        opts['default_width'] = "auto"
        opts['width'] = "100%"
        opts['height'] = "100%"
        opts['query']={}
        opts['query']['inclusions']=[]
        
        opts['id'] = "disp_list_%s_%s" % (disp_list_guid,random.randint(10000,99999))
        try:
            # reverse lookup of the datagrid-list url (see dojango/urls.py)
            if self.model:
                opts['json_store_url'] = reverse("dojango-datagrid-list", args=(self.app_name, self.model_name))
        except NoReverseMatch:
            pass
        
        # User overrides
        if self.options:
            opts.update(extract_nodelist_options(self.options,context))
        if not opts['query'].has_key('inclusions'): opts['query']['inclusions'] = []
            
        # we must ensure that the json_store_url is defined
        if not opts.get('json_store_url', False):
            raise TemplateSyntaxError, "Please enable the url 'dojango-datagrid-list' in your urls.py or pass a 'json_store_url' to the datagrid templatetag."
        
        # Incase list_display was passed as tuple, turn to list for mutability
        if not self.model and not opts.get('list_display', False):
            raise TemplateSyntaxError, "'list_display' not defined. If you use your own 'json_store_url' you have to define which fields are visible."
        opts['list_display'] = list(opts['list_display'])
        
        # Config for template
        opts['headers'] = []

        # Get field labels using verbose name (take into account i18n), will be used
        # for column labels
        verbose_field_names = {}
        if self.model:
            verbose_field_names = dict([(f.name, f.verbose_name) for f in self.model._meta.fields])

        for field in opts['list_display']:
            ret = {'attname':field}
            for q in FIELD_ATTRIBUTES:
                if opts.has_key(q) and opts[q].has_key(field):
                     ret[q] = opts[q][field]
            # custom default logic
            if not ret.has_key('label'):
                ret['label'] = verbose_field_names.get(field, field.replace('_', ' '))
            if not ret.has_key('column_width'):
                ret['column_width']= opts['default_width']
            # add as inclusion if not a attribute of model
            if self.model and not field in map(lambda x: x.attname, self.model._meta.fields):
                opts['query']['inclusions'].append(field)
            # add to header
            opts['headers'].append(ret)
              
        # no sort fields
        if opts.has_key("nosort"): 
            opts['nosort'] = "".join(["||row==%s"%(opts['list_display'].index(r)+1) for r in opts['nosort']])
        
        # additional context info/modifications
        opts["model_name"] = self.model_name
        opts["app_name"] = self.app_name
        opts['query']['inclusions'] = ",".join(opts['query']['inclusions'])
        if opts.has_key('search'):
            opts['search_fields'] = ",".join(opts['search'])
            opts['show_search'] = opts.get('show_search', True)
        else:
            opts['show_search'] = False

        # return rendered template
        return get_template("dojango/templatetag/datagrid_disp.html").render(template.Context(opts))
