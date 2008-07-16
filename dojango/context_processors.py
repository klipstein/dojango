from dojango.util.config import Config

def config(request):
    '''Make several dojango constants available in the template, like:
      
      {{ DOJANGO.DOJO_BASE_URL }}, {{ DOJANGO.DOJO_URL }}, ...
      
    You can also use the templatetag 'set_dojango_context' in your templates.
    Just set the following at the top of your template to set these context
    contants:
    
    If you want to use the default DOJANGO_DOJO_VERSION/DOJANGO_DOJO_PROFILE:
    
      {% load dojango_base %}
      {% set_dojango_context %}
      
    Using a difernet profile set the following:
    
      {% load dojango_base %}
      {% set_dojango_context "google" "1.1.1" %} 
    '''
    context_extras = {'DOJANGO': {}}
    config = Config()
    context_extras['DOJANGO'] = config.get_context_dict()
    return context_extras