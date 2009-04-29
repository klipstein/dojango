from django import template
from django.db.models import get_model
from django.db import models
from django.template.loader import get_template

from dojango.util import json_response, to_dojo_data, json_encode
from dojango.util.dojo_collector import add_module
from dojango.conf import settings # using the app-specific settings

import random

register = template.Library()
disp_list_guid = 0

@register.tag
def simple_datagrid(parser,token):
    bits = token.split_contents()
    return DatagridNode(bits[1],bits[2],None)

@register.tag
def datagrid(parser,token):
    bits = token.split_contents()
    nodelist = parser.parse(('enddatagrid',))
    parser.delete_first_token()
    return DatagridNode(bits[1],bits[2],nodelist)
    
class DatagridNode(template.Node):
    def __init__(self,app, model,options):
        self.model = get_model(app,model)
        self.app_name = app
        self.model_name = model
        self.options = options
        
    def render(self,context):
        opts = {}
        global disp_list_guid
        disp_list_guid = disp_list_guid +1
        # add dojo modules
        add_module("dojox.data.QueryReadStore")
        add_module("dojox.grid.DataGrid")
        
        # Setable options, not listed: label, query, search
        ## TODO, nosort
        opts['list_display'] = [x.attname for x in self.model._meta.fields]
        opts['column_width'] = {}
        opts['default_width'] = "auto"
        opts['width'] = "100%"
        opts['height'] = "100%"
        opts['id'] = "disp_list_%s_%s"%(disp_list_guid,random.randint(10000,99999))
        
        # User overrides
        if self.options:
            insides = self.options.render(context)
            if insides.find('=')>0:
                for key,val in [ opt.strip().split("=") for opt in insides.split("\n") if opt.find('=')>-1 ]:
                    opts[key.strip()]=eval(val.strip())
        
        # Config for template
        opts['headers'] = []
        for f in opts['list_display']:
            field = [x for x in self.model._meta.fields if x.attname==f]
            if len(field)>0:
                f = field[0]
                if opts['column_width'].has_key(f.attname): 
                     f.width = opts['column_width'][f.attname]
                else: f.width= opts['default_width']
                if opts.has_key('label') and opts['label'].has_key(f.attname):
                    f.label = opts['label'][f.attname]
                else:
                    f.label = f.name.replace('_', ' ')
                opts['headers'].append(f)
            else:
                tmp = {'attname':f}
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

        # additional context info
        opts["model_name"] = self.model_name
        opts["app_name"] = self.app_name
        if opts.has_key('query') and opts['query'].has_key("inclusions"):
             opts['query']['inclusions'] = ",".join(opts['query']['inclusions'])
        # generate js search query
        if opts.has_key('search'):  opts['search_fields'] = ",".join(opts['search'])
        # return rendered template
        return get_template("dojango/templatetag/datagrid_disp.html").render(template.Context(opts))