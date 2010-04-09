# Create your views here.
from django.db.models import get_model
from django.db import models
from django.shortcuts import render_to_response
from django.conf import settings

from dojango.util import to_dojo_data, json_encode
from dojango.decorators import json_response
from dojango.util import to_dojo_data
from dojango.util.form import get_combobox_data
from dojango.util.perms import access_model, access_model_field

import operator
    
# prof included for people using http://www.djangosnippets.org/snippets/186/
AVAILABLE_OPTS =  ('search_fields','prof','inclusions','sort','search','count','order','start')

@json_response
def datagrid_list(request, app_name, model_name, access_model_callback=access_model, access_field_callback=access_model_field):
    """
    Renders a json representation of a model within an app.  Set to handle GET params passed
    by dojos ReadQueryStore for the dojango datagrid.  The following GET params are handled with
    specially:
      'search_fields','inclusions','sort','search','count','order','start'
      
    search_fields: list of fields for model to equal the search, each OR'd together.
    search: see search_fields
    sort: sets order_by
    count: sets limit
    start: sets offset
    inclusions: list of functions in the model that will be called and result added to JSON
     
    any other GET param will be added to the filter on the model to determine what gets returned.  ie
    a GET param of id__gt=5 will result in the equivalent of model.objects.all().filter( id__gt=5 )
    
    The access_model_callback is a function that gets passed the request, app_name, model_name, and
    an instance of the model which will only be added to the json response if returned True
    
    The access_field_callback gets passed the request, app_name, model_name, field_name,
    and the instance.  Return true to allow access of a given field_name to model 
    app_name.model_name given instance model.
    
    The default callbacks will allow access to any model in added to the DOJANGO_DATAGRID_ACCESS
    in settings.py and any function/field that is not "delete"
    """
    
    # get the model
    model = get_model(app_name,model_name)
    
    # start with a very broad query set
    target = model.objects.all()
    
    # modify query set based on the GET params, dont do the start/count splice
    # custom options passed from "query" param in datagrid
    for key in [ d for d in request.GET.keys() if not d in AVAILABLE_OPTS]:
        target = target.filter(**{str(key):request.GET[key]})
    num = target.count()

    # until after all clauses added
    if request.GET.has_key('search') and request.GET.has_key('search_fields'):
        ored = [models.Q(**{str(k).strip(): unicode(request.GET['search'])} ) for k in request.GET['search_fields'].split(",")]
        target = target.filter(reduce(operator.or_, ored))

    if request.GET.has_key('sort') and request.GET["sort"] not in request.GET["inclusions"] and request.GET["sort"][1:] not in request.GET["inclusions"]:
		# if the sort field is in inclusions, it must be a function call.. 
        target = target.order_by(request.GET['sort'])
    else:
		if request.GET.has_key('sort') and request.GET["sort"].startswith('-'):
			target = sorted(target, lambda x,y: cmp(getattr(x,request.GET["sort"][1:])(),getattr(y,request.GET["sort"][1:])()));
			target.reverse();
		elif request.GET.has_key('sort'):
			target =  sorted(target, lambda x,y: cmp(getattr(x,request.GET["sort"])(),getattr(y,request.GET["sort"])()));
    
    
    # get only the limit number of models with a given offset
    target=target[int(request.GET['start']):int(request.GET['start'])+int(request.GET['count'])]
    # create a list of dict objects out of models for json conversion
    complete = []
    for data in target:
        # TODO: complete rewrite to use dojangos already existing serializer (or the dojango ModelStore)
        if access_model_callback(app_name, model_name, request, data):   
            ret = {}
            for f in data._meta.fields:
                if access_field_callback(app_name, model_name, f.attname, request, data):
                    if isinstance(f, models.ImageField) or isinstance(f, models.FileField): # filefields can't be json serialized
                        ret[f.attname] = unicode(getattr(data, f.attname))
                    else:
                        ret[f.attname] = getattr(data, f.attname) #json_encode() this?
            fields = dir(data.__class__) + ret.keys()
            add_ons = [k for k in dir(data) if k not in fields and access_field_callback(app_name, model_name, k, request, data)]
            for k in add_ons:
                ret[k] = getattr(data, k)
            if request.GET.has_key('inclusions'):
                for k in request.GET['inclusions'].split(','):
                    if k == "": continue
                    if access_field_callback(app_name, model_name, k, request, data): 
                        try:
                            ret[k] = getattr(data,k)()
                        except:
                            try:
                                ret[k] = eval("data.%s"%".".join(k.split("__")))
                            except:
                                ret[k] = getattr(data,k)
            complete.append(ret)
        else:
            raise Exception, "You're not allowed to query the model '%s.%s' (add it to the array of the DOJANGO_DATAGRID_ACCESS setting)" % (model_name, app_name)
    return to_dojo_data(complete, identifier=model._meta.pk.name, num_rows=num)

###########
#  Tests  #
###########

def test(request):
    return render_to_response('dojango/test.html')

@json_response
def test_countries(request):
    countries = { 'identifier': 'name',
                  'label': 'name',
                  'items': [
                      { 'name':'Africa', 'type':'continent', 'population':'900 million', 'area': '30,221,532 sq km',
                         'timezone': '-1 UTC to +4 UTC',
                          'children':[{'_reference':'Egypt'}, {'_reference':'Kenya'}, {'_reference':'Sudan'}] },
                      { 'name':'Egypt', 'type':'country' },
                      { 'name':'Kenya', 'type':'country',
                          'children':[{'_reference':'Nairobi'}, {'_reference':'Mombasa'}] },
                      { 'name':'Nairobi', 'type':'city' },
                      { 'name':'Mombasa', 'type':'city' },
                      { 'name':'Sudan', 'type':'country',
                          'children':{'_reference':'Khartoum'} },
                      { 'name':'Khartoum', 'type':'city' },
                      { 'name':'Asia', 'type':'continent',
                          'children':[{'_reference':'China'}, {'_reference':'India'}, {'_reference':'Russia'}, {'_reference':'Mongolia'}] },
                      { 'name':'China', 'type':'country' },
                      { 'name':'India', 'type':'country' },
                      { 'name':'Russia', 'type':'country' },
                      { 'name':'Mongolia', 'type':'country' },
                      { 'name':'Australia', 'type':'continent', 'population':'21 million',
                          'children':{'_reference':'Commonwealth of Australia'}},
                      { 'name':'Commonwealth of Australia', 'type':'country', 'population':'21 million'},
                      { 'name':'Europe', 'type':'continent',
                          'children':[{'_reference':'Germany'}, {'_reference':'France'}, {'_reference':'Spain'}, {'_reference':'Italy'}] },
                      { 'name':'Germany', 'type':'country' },
                      { 'name':'Spain', 'type':'country' },
                      { 'name':'Italy', 'type':'country' },
                      { 'name':'North America', 'type':'continent',
                          'children':[{'_reference':'Mexico'}, {'_reference':'Canada'}, {'_reference':'United States of America'}] },
                      { 'name':'Mexico', 'type':'country',  'population':'108 million', 'area':'1,972,550 sq km',
                          'children':[{'_reference':'Mexico City'}, {'_reference':'Guadalajara'}] },
                      { 'name':'Mexico City', 'type':'city', 'population':'19 million', 'timezone':'-6 UTC'},
                      { 'name':'Guadalajara', 'type':'city', 'population':'4 million', 'timezone':'-6 UTC' },
                      { 'name':'Canada', 'type':'country',  'population':'33 million', 'area':'9,984,670 sq km',
                          'children':[{'_reference':'Ottawa'}, {'_reference':'Toronto'}] },
                      { 'name':'Ottawa', 'type':'city', 'population':'0.9 million', 'timezone':'-5 UTC'},
                      { 'name':'Toronto', 'type':'city', 'population':'2.5 million', 'timezone':'-5 UTC' },
                      { 'name':'United States of America', 'type':'country' },
                      { 'name':'South America', 'type':'continent',
                          'children':[{'_reference':'Brazil'}, {'_reference':'Argentina'}] },
                      { 'name':'Brazil', 'type':'country', 'population':'186 million' },
                      { 'name':'Argentina', 'type':'country', 'population':'40 million' },
                  ]
                  }

    return countries

@json_response
def test_states(request):
    states = [
        {'name':"Alabama", 'label':"<img width='97px' height='127px' src='images/Alabama.jpg'/>Alabama",'abbreviation':"AL"},
        {'name':"Alaska", 'label':"Alaska",'abbreviation':"AK"},
        {'name':"American Samoa", 'label':"American Samoa",'abbreviation':"AS"},
        {'name':"Arizona", 'label':"Arizona",'abbreviation':"AZ"},
        {'name':"Arkansas", 'label':"Arkansas",'abbreviation':"AR"},
        {'name':"Armed Forces Europe", 'label':"Armed Forces Europe",'abbreviation':"AE"},
        {'name':"Armed Forces Pacific", 'label':"Armed Forces Pacific",'abbreviation':"AP"},
        {'name':"Armed Forces the Americas", 'label':"Armed Forces the Americas",'abbreviation':"AA"},
        {'name':"California", 'label':"California",'abbreviation':"CA"},
        {'name':"Colorado", 'label':"Colorado",'abbreviation':"CO"},
        {'name':"Connecticut", 'label':"Connecticut",'abbreviation':"CT"},
        {'name':"Delaware", 'label':"Delaware",'abbreviation':"DE"},
        {'name':"District of Columbia", 'label':"District of Columbia",'abbreviation':"DC"},
        {'name':"Federated States of Micronesia", 'label':"Federated States of Micronesia",'abbreviation':"FM"},
        {'name':"Florida", 'label':"Florida",'abbreviation':"FL"},
        {'name':"Georgia", 'label':"Georgia",'abbreviation':"GA"},
        {'name':"Guam", 'label':"Guam",'abbreviation':"GU"},
        {'name':"Hawaii", 'label':"Hawaii",'abbreviation':"HI"},
        {'name':"Idaho", 'label':"Idaho",'abbreviation':"ID"},
        {'name':"Illinois", 'label':"Illinois",'abbreviation':"IL"},
        {'name':"Indiana", 'label':"Indiana",'abbreviation':"IN"},
        {'name':"Iowa", 'label':"Iowa",'abbreviation':"IA"},
        {'name':"Kansas", 'label':"Kansas",'abbreviation':"KS"},
        {'name':"Kentucky", 'label':"Kentucky",'abbreviation':"KY"},
        {'name':"Louisiana", 'label':"Louisiana",'abbreviation':"LA"},
        {'name':"Maine", 'label':"Maine",'abbreviation':"ME"},
        {'name':"Marshall Islands", 'label':"Marshall Islands",'abbreviation':"MH"},
        {'name':"Maryland", 'label':"Maryland",'abbreviation':"MD"},
        {'name':"Massachusetts", 'label':"Massachusetts",'abbreviation':"MA"},
        {'name':"Michigan", 'label':"Michigan",'abbreviation':"MI"},
        {'name':"Minnesota", 'label':"Minnesota",'abbreviation':"MN"},
        {'name':"Mississippi", 'label':"Mississippi",'abbreviation':"MS"},
        {'name':"Missouri", 'label':"Missouri",'abbreviation':"MO"},
        {'name':"Montana", 'label':"Montana",'abbreviation':"MT"},
        {'name':"Nebraska", 'label':"Nebraska",'abbreviation':"NE"},
        {'name':"Nevada", 'label':"Nevada",'abbreviation':"NV"},
        {'name':"New Hampshire", 'label':"New Hampshire",'abbreviation':"NH"},
        {'name':"New Jersey", 'label':"New Jersey",'abbreviation':"NJ"},
        {'name':"New Mexico", 'label':"New Mexico",'abbreviation':"NM"},
        {'name':"New York", 'label':"New York",'abbreviation':"NY"},
        {'name':"North Carolina", 'label':"North Carolina",'abbreviation':"NC"},
        {'name':"North Dakota", 'label':"North Dakota",'abbreviation':"ND"},
        {'name':"Northern Mariana Islands", 'label':"Northern Mariana Islands",'abbreviation':"MP"},
        {'name':"Ohio", 'label':"Ohio",'abbreviation':"OH"},
        {'name':"Oklahoma", 'label':"Oklahoma",'abbreviation':"OK"},
        {'name':"Oregon", 'label':"Oregon",'abbreviation':"OR"},
        {'name':"Pennsylvania", 'label':"Pennsylvania",'abbreviation':"PA"},
        {'name':"Puerto Rico", 'label':"Puerto Rico",'abbreviation':"PR"},
        {'name':"Rhode Island", 'label':"Rhode Island",'abbreviation':"RI"},
        {'name':"South Carolina", 'label':"South Carolina",'abbreviation':"SC"},
        {'name':"South Dakota", 'label':"South Dakota",'abbreviation':"SD"},
        {'name':"Tennessee", 'label':"Tennessee",'abbreviation':"TN"},
        {'name':"Texas", 'label':"Texas",'abbreviation':"TX"},
        {'name':"Utah", 'label':"Utah",'abbreviation':"UT"},
        {'name':"Vermont", 'label':"Vermont",'abbreviation':"VT"},
        {'name': "Virgin Islands, U.S.",'label':"Virgin Islands, U.S.",'abbreviation':"VI"},
        {'name':"Virginia", 'label':"Virginia",'abbreviation':"VA"},
        {'name':"Washington", 'label':"Washington",'abbreviation':"WA"},
        {'name':"West Virginia", 'label':"West Virginia",'abbreviation':"WV"},
        {'name':"Wisconsin", 'label':"Wisconsin",'abbreviation':"WI"},
        {'name':"Wyoming", 'label':"Wyoming",'abbreviation':"WY"}
    ]
    # Implement a very simple search!
    search_string, start, end = get_combobox_data(request)
    ret = []
    for state in states:
        if state['name'].lower().startswith(search_string.lower()):
            ret.append(state)
    ret = ret[start:end]
    
    # Convert the data into dojo.date-store compatible format.
    return to_dojo_data(ret, identifier='abbreviation')
