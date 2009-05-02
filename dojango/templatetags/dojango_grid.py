from django import template
from django.db.models import get_model
from django.db import models
from django.template import TemplateSyntaxError
from django.template.loader import get_template

from dojango.util import json_response, to_dojo_data, json_encode
from dojango.util.dojo_collector import add_module
from dojango.util.perms import access_model
from django.core.urlresolvers import reverse, NoReverseMatch

import random

register = template.Library()
disp_list_guid = 0

@register.tag
def simple_datagrid(parser, token):
    """
    Generates a dojo datagrid for a given app's model.
    i.e.  {% simple_datagrid myapp mymodel %}
    """
    bits = token.split_contents()
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
    return DatagridNode(bits[1],bits[2],nodelist)
    
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
    nosort:            fields not to sort on
    formatter:         dict of attribute:js formatter function
    json_store_url:    URL for the ReadQueryStore 
    """
    def __init__(self, app, model, options):
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
        add_module("dojox.layout.ContentPane")
        
        # Setable options, not listed: label, query, search, nosort
        opts['list_display'] = [x.attname for x in self.model._meta.fields]
        opts['column_width'] = {}
        opts['default_width'] = "auto"
        opts['width'] = "100%"
        opts['height'] = "100%"
        opts['id'] = "disp_list_%s_%s" % (disp_list_guid,random.randint(10000,99999))
        try:
            # reverse lookup of the datagrid-list url (see dojango/urls.py)
            opts['json_store_url'] = reverse("dojango-datagrid-list", args=(self.app_name, self.model_name))
        except NoReverseMatch:
            pass
        # User overrides
        if self.options:
            insides = self.options.render(context)
            if insides.find('=')>0:
                for key,val in [ opt.strip().split("=") for opt in insides.split("\n") if opt.find('=')>-1 ]:
                    opts[key.strip()]=eval(val.strip())
        # we must ensure that the json_store_url is defined
        if not opts.get('json_store_url', False):
            raise TemplateSyntaxError, "Please enable the url 'dojango-datagrid-list' in your urls.py or pass a 'json_store_url' to the datagrid templatetag."
        opts['list_display'] = list(opts['list_display'])
        # Config for template
        opts['headers'] = []
        for f in opts['list_display']:
            field = [x for x in self.model._meta.fields if x.attname==f]
            if len(field)>0:
                ## Add as Field
                f = field[0]
                if opts['column_width'].has_key(f.attname): 
                     f.width = opts['column_width'][f.attname]
                else: f.width= opts['default_width']
                if opts.has_key('label') and opts['label'].has_key(f.attname):
                    f.label = opts['label'][f.attname]
                else:
                    f.label = f.name.replace('_', ' ')
                if opts.has_key('formatter') and opts['formatter'].has_key(f.attname):
                    f.formatter = opts['formatter'][f.attname]
                opts['headers'].append(f)
            else:
                ## Create Dict with same attributes as Field that is used by template
                tmp = {'attname':f}
                if opts.has_key('formatter') and opts['formatter'].has_key(f):
                    tmp['formatter'] = opts['formatter'][f]
                if opts.has_key('label') and opts['label'].has_key(f):
                    tmp['label'] = opts['label'][f]
                else:
                    try:
                        tmp['label'] = getattr(self.model, f).short_description
                    except AttributeError:
                        tmp['label'] = f.replace('_', ' ')  
                if opts['column_width'].has_key(f): 
                    tmp['width']=opts['column_width'][f]
                else: 
                    tmp['width']= opts['default_width']
                if not opts.has_key("query"): opts['query']={}
                if not opts['query'].has_key("inclusions"): opts['query']['inclusions']=[]
                opts['query']['inclusions'].append(f)
                opts['headers'].append(tmp)
        if opts.has_key("nosort"): 
            opts['nosort'] = "".join(["||row==%s"%(opts['list_display'].index(r)+1) for r in opts['nosort']])
        # additional context info
        opts["model_name"] = self.model_name
        opts["app_name"] = self.app_name
        if opts.has_key('query') and opts['query'].has_key("inclusions"):
             opts['query']['inclusions'] = ",".join(opts['query']['inclusions'])
        # generate js search query
        if opts.has_key('search'):  opts['search_fields'] = ",".join(opts['search'])
        # return rendered template
        return get_template("dojango/templatetag/datagrid_disp.html").render(template.Context(opts))