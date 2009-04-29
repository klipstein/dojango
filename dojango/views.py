# Create your views here.
from django.db.models import get_model
from django.db import models
from django.shortcuts import render_to_response

from dojango.util import json_response, to_dojo_data, json_encode
from dojango.decorators import json_response
from dojango.util import to_dojo_data
from dojango.util.form import get_combobox_data

import operator

# prof included for people using http://www.djangosnippets.org/snippets/186/
AVAILABLE_OPTS =  ('search_fields','prof','inclusions','sort','search','count','order','start') 
    
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

@json_response
def disp(request,app_name, model_name):
    #####################################
    ###  WARNING: Security... yikes   ###
    #####################################
    
    # get the model
    model = get_model(app_name,model_name)
    
    # start with a very broad query set
    target = model.objects.all()
    
    # modify query set based on the GET params, dont do the start/count splice
    # until after all clauses added
    if request.GET.has_key('sort'):
        target = target.order_by(request.GET['sort'])
    
    if request.GET.has_key('search') and request.GET.has_key('search_fields'):
        ored = [models.Q(**{str(k).strip(): str(request.GET['search'])} ) for k in request.GET['search_fields'].split(",")]
        target = target.filter(reduce(operator.or_, ored))
    
    # custom options passed from "query" param in datagrid
    for key in [ d for d in request.GET.keys() if not d in AVAILABLE_OPTS]:
        target = target.filter(**{str(key):request.GET[key]})
    # get only the limit number of models with a given offset
    target=target[request.GET['start']:int(request.GET['start'])+int(request.GET['count'])]
    
    # create a list of dict objects out of models for json conversion
    complete = []
    for data in target:        
        ret = {}
        for f in data._meta.fields:
            ret[f.attname] = getattr(data, f.attname) #json_encode() this?
        fields = dir(data.__class__) + ret.keys()
        add_ons = [k for k in dir(data) if k not in fields]
        for k in add_ons:
            ret[k] = _any(getattr(data, k))
        if request.GET.has_key('inclusions'):
            for k in request.GET['inclusions'].split(','):
                ret[k] = getattr(data,k)()
        complete.append(ret)
    return to_dojo_data(complete, num_rows=len(complete))