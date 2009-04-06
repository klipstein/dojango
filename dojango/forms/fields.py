# require all default django forms to use them as fallback
from django.forms import fields

from dojango.forms import widgets
from dojango.util import json_encode


__all__ = ['DojoFieldMixin', 'CharField', 'ChoiceField', 'TypedChoiceField',
           'IntegerField', 'BooleanField', 'FileField', 'ImageField',
           'DateField', 'TimeField', 'DateTimeField', 'SplitDateTimeField',
           'RegexField', 'DecimalField', 'FloatField', 'FilePathField',
           'MultipleChoiceField', 'NullBooleanField', 'EmailField',
           'IPAddressField', 'URLField', 'SlugField', 'MultiValueField', 
           'ComboField', ]

class DojoFieldMixin(object):
    # the following field attributes will be passed
    # to the widgets. the widget will then evaluate
    # which of these parameters will be used.
    passed_attrs = [
        'required',
        'help_text',
        'min_value',
        'max_value',
        'max_length',
        'max_digits',
        'decimal_places',
        'js_regex', # special key for some dojo widgets
    ]
    
    def widget_attrs(self, widget):
        ret = {'extra_field_attrs': {}}
        for field_attr in self.passed_attrs:
            field_val = getattr(self, field_attr, None)
            #print field_attr, widget, field_val
            if field_val is not None:
                ret['extra_field_attrs'][field_attr] = field_val
        return ret

class CharField(DojoFieldMixin, fields.CharField):
    widget = widgets.TextInput

class ChoiceField(DojoFieldMixin, fields.ChoiceField):
    widget = widgets.Select
    
class TypedChoiceField(DojoFieldMixin, fields.TypedChoiceField):
    widget = widgets.Select

class IntegerField(DojoFieldMixin, fields.IntegerField):
    widget = widgets.NumberTextInput
    decimal_places = 0

class BooleanField(DojoFieldMixin, fields.BooleanField):
    widget = widgets.CheckboxInput

class FileField(DojoFieldMixin, fields.FileField):
    widget = widgets.FileInput
    
class ImageField(DojoFieldMixin, fields.ImageField):
    widget = widgets.FileInput

class DateField(CharField):
    widget = widgets.DateInput

class TimeField(CharField):
    widget = widgets.TimeInput

class DateTimeField(CharField):
    widget = widgets.DateTimeInput
    
SplitDateTimeField = DateTimeField # datetime input is always splitted
    
class RegexField(DojoFieldMixin, fields.RegexField):
    widget = widgets.ValidationTextInput
    js_regex = None
    
    def __init__(self, js_regex=None, *args, **kwargs):
        self.js_regex = js_regex
        super(RegexField, self).__init__(*args, **kwargs)
        
class DecimalField(DojoFieldMixin, fields.DecimalField):
    widget = widgets.NumberTextInput

class FloatField(DojoFieldMixin, fields.FloatField):
    widget = widgets.ValidationTextInput
    
class FilePathField(DojoFieldMixin, fields.FilePathField):
    widget = widgets.Select
    
class MultipleChoiceField(DojoFieldMixin, fields.MultipleChoiceField):
    widget = widgets.SelectMultiple
    
class NullBooleanField(DojoFieldMixin, fields.NullBooleanField):
    widget = widgets.NullBooleanSelect
    
class EmailField(DojoFieldMixin, fields.EmailField):
    widget = widgets.EmailTextInput
    
class IPAddressField(DojoFieldMixin, fields.IPAddressField):
    widget = widgets.IPAddressTextInput
    
class URLField(DojoFieldMixin, fields.URLField):
    widget = widgets.URLTextInput

class SlugField(DojoFieldMixin, fields.SlugField):
    widget = widgets.ValidationTextInput
    js_regex = '^[-\w]+$' # we cannot extract the original regex input from the python regex
    
MultiValueField = fields.MultiValueField

ComboField = fields.MultiValueField