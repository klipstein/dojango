# require all default django forms to use them as fallback
from django.forms import fields

from dojango.forms import widgets
from dojango.util import json_encode


__all__ = ['DojoFieldMixin', 'CharField', 'ChoiceField', 'TypedChoiceField',
           'IntegerField', 'BooleanField', 'FileField', 'ImageField',
           'DateField', 'TimeField', 'DateTimeField', 'SplitDateTimeField',
           'RegexField', 'DecimalField', 'FloatField', 'FilePathField',
           'MultipleChoiceField', 'NullBooleanField', 'EmailField',
           'IPAddressField', 'URLField', 'MultiValueField', 'ComboField',]

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
    # TODO: remove that dependency
    dojo_attrs = {
        'required':'required',
        'help_text':'promptMessage',
        'min_value':'constraints.min',
        'max_value':'constraints.max',
        'max_length':'maxLength',
        'max_digits':'maxDigits',
        'decimal_places':'decimalPlaces',
        'js_regex':'regExp',
    }
    
    def widget_attrs(self, widget):
        ret = {'extra_attrs': {}}
        for field_attr in self.passed_attrs:
            field_val = getattr(self, field_attr, None)
            #print field_val, field_attr
            if field_val is not None:
                ret['extra_attrs'][field_attr] = field_val
        '''if getattr(self, "extra_dojo_attrs", False):
            self.dojo_attrs.update(self.extra_dojo_attrs)'''
        '''for field_attr in self.dojo_attrs:
            field_val = getattr(self, field_attr, None)
            if field_val is not None:
                dojo_field_attr = self.dojo_attrs[field_attr].split(".")
                inner_dict = ret
                len_fields = len(dojo_field_attr)
                count = 0
                for i in dojo_field_attr:
                    count = count+1
                    if count == len_fields:
                        inner_dict[i] = field_val
                    elif not inner_dict.has_key(i):
                        inner_dict[i] = {}
                    inner_dict = inner_dict[i]'''
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
    
MultiValueField = fields.MultiValueField

ComboField = fields.MultiValueField