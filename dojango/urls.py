import os

from django.conf.urls.defaults import *
from django.conf import settings

from dojango.util import media

urlpatterns = patterns('dojango',
    url(r'^test/$', 'views.test', name='dojango-test'),
    url(r'^test/countries/$', 'views.test_countries'),
    url(r'^test/states/$', 'views.test_states'),
    # Note: define accessible objects in DOJANGO_DATAGRID_ACCESS setting
    url(r'^datagrid-list/(?P<app_name>.+)/(?P<model_name>.+)/$', 'views.datagrid_list', name="dojango-datagrid-list"),
)

if settings.DEBUG:
    # serving the media files for dojango / dojo (js/css/...)
    urlpatterns += media.url_patterns
