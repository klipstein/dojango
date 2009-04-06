from django.forms import widgets
from django.utils.encoding import StrAndUnicode, force_unicode
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.utils import datetime_safe

from dojango.util.config import Config

from dojango.forms import collector

__all__ = [ 'DojoWidgetMixin', 'Input', 'Widget', 'TextInput', 'PasswordInput',
            'HiddenInput', 'MultipleHiddenInput', 'FileInput', 'Textarea',
            'DateInput', 'DateTimeInput', 'TimeInput', 'CheckboxInput', 'Select', 
            'NullBooleanSelect', 'SelectMultiple', 'RadioInput', 'RadioFieldRenderer',
            'RadioSelect', 'CheckboxSelectMultiple', 'MultiWidget', 'SplitDateTimeWidget',
            'SplitHiddenDateTimeWidget', 'EditorInput', 'HorizontalSliderInput',
            'VerticalSliderInput', 'ValidationTextInput', 'ValidationPasswordInput',
            'EmailTextInput', 'IPAddressTextInput', 'URLTextInput', 'NumberTextInput',
            'RangeBoundTextInput', 'NumberSpinnerInput', 'RatingInput']

dojo_config = Config() # initialize the configuration

class DojoWidgetMixin:
    dojo_type = None
    valid_extra_attrs = []
    extra_dojo_require = []
    alt_require = None # alternative dojo.require call (not using the dojo_type)
    
    default_field_attr_map = { # the default map for mapping field attributes to dojo attributes
        'required':'required',
        'help_text':'promptMessage',
        'min_value':'constraints.min',
        'max_value':'constraints.max',
        'max_length':'maxlength',
        #'max_digits':'maxDigits',
        'decimal_places':'constraints.places',
        'js_regex':'regExp',
    }
    field_attr_map = {} # used for overwriting the default attr-map
    
    def _mixin_attr(self, attrs, value, key):
        dojo_field_attr = key.split(".")
        inner_dict = attrs
        len_fields = len(dojo_field_attr)
        count = 0
        for i in dojo_field_attr:
            count = count+1
            if count == len_fields and inner_dict.get(i, None) is None:
                inner_dict[i] = value
            elif not inner_dict.has_key(i):
                inner_dict[i] = {}
            inner_dict = inner_dict[i]
        return attrs
    
    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        # gathering all widget attributes
        attrs = dict(self.attrs, **kwargs)
        self.default_field_attr_map.update(self.field_attr_map) # the field-attribute-mapping can be customzied
        if extra_attrs:
            attrs.update(extra_attrs)
        
        # assigning dojoType to our widget
        dojo_type = getattr(self, "dojo_type", False)
        if dojo_type:
            attrs["dojoType"] = dojo_type # add the dojoType attribute
            
        # fill the global collector object
        if getattr(self, "alt_require", False):
            collector.add_module(self.alt_require)
        elif dojo_type:
            collector.add_module(self.dojo_type)
        extra_requires = getattr(self, "extra_dojo_require", [])
        for i in extra_requires:
            collector.add_module(i)
        
        # 
        extra_field_attrs = attrs.get("extra_field_attrs", False)
        if extra_field_attrs:
            for i in self.valid_extra_attrs:
                field_val = extra_field_attrs.get(i, None)
                new_attr_name = self.default_field_attr_map.get(i, None)
                if field_val is not None and new_attr_name is not None:
                    attrs = self._mixin_attr(attrs, field_val, new_attr_name)
            del attrs["extra_field_attrs"]
        return attrs

class Widget(DojoWidgetMixin, widgets.Widget):
    dojo_type = 'dijit._Widget'

class Input(DojoWidgetMixin, widgets.Input):
    pass

class TextInput(DojoWidgetMixin, widgets.TextInput):
    dojo_type = 'dijit.form.TextBox'
    valid_extra_attrs = [
        'max_length',
    ]

class PasswordInput(DojoWidgetMixin, widgets.PasswordInput):
    dojo_type = 'dijit.form.TextBox'
    valid_extra_attrs = [
        'max_length',
    ]

class HiddenInput(DojoWidgetMixin, widgets.HiddenInput):
    dojo_type = None

class MultipleHiddenInput(DojoWidgetMixin, widgets.MultipleHiddenInput):
    dojo_type = None

class FileInput(DojoWidgetMixin, widgets.FileInput):
    dojo_type = 'dojox.form.FileInput'
    class Media:
        css = {
            'all': ('%(base_url)s/dojox/form/resources/FileInput.css' % {
                'base_url':dojo_config.dojo_base_url
            },)
        }

class Textarea(DojoWidgetMixin, widgets.Textarea):
    dojo_type = 'dijit.form.Textarea'

class DateInput(TextInput):
    dojo_type = 'dijit.form.DateTextBox'
    valid_extra_attrs = [
        'required',
        'help_text',
    ]
    format = '%Y-%m-%d'     # '2006-10-25'
    def __init__(self, attrs=None, format=None):
        super(DateInput, self).__init__(attrs)
        if format:
            self.format = format

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        elif hasattr(value, 'strftime'):
            value = datetime_safe.new_date(value)
            value = value.strftime(self.format)
        return super(DateInput, self).render(name, value, attrs)

class TimeInput(TextInput):
    dojo_type = 'dijit.form.TimeTextBox'
    valid_extra_attrs = [
        'required',
        'help_text',
    ]
    format = "T%H:%M:%S"    # special for dojo: 'T12:12:33'
    def __init__(self, attrs=None, format=None):
        super(TimeInput, self).__init__(attrs)
        if format:
            self.format = format

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        elif hasattr(value, 'strftime'):
            value = value.strftime(self.format)
        return super(TimeInput, self).render(name, value, attrs)

class CheckboxInput(DojoWidgetMixin, widgets.CheckboxInput):
    dojo_type = 'dijit.form.CheckBox'

class Select(DojoWidgetMixin, widgets.Select):
    dojo_type = 'dijit.form.FilteringSelect'
    valid_extra_attrs = [
        'required',
        'help_text',
    ]

class NullBooleanSelect(DojoWidgetMixin, widgets.NullBooleanSelect):
    dojo_type = 'dijit.form.FilteringSelect'

class SelectMultiple(DojoWidgetMixin, widgets.SelectMultiple):
    dojo_type = 'dijit.form.MultiSelect'

RadioInput = widgets.RadioInput    
RadioFieldRenderer = widgets.RadioFieldRenderer

class RadioSelect(DojoWidgetMixin, widgets.RadioSelect):
    dojo_type = 'dijit.form.RadioButton'
    
    def __init__(self, attrs=None):
        if dojo_config.version < '1.3.0':
            self.alt_require = 'dijit.form.CheckBox'
        super(RadioSelect, self).__init__(attrs)

class CheckboxSelectMultiple(DojoWidgetMixin, widgets.CheckboxSelectMultiple):
    dojo_type = 'dijit.form.CheckBox'
    
class MultiWidget(DojoWidgetMixin, widgets.MultiWidget):
    dojo_type = None

class SplitDateTimeWidget(widgets.SplitDateTimeWidget):
    """
    DateTimeInput is using two input fields.
    """
    date_format = DateInput.format
    time_format = TimeInput.format
    
    def __init__(self, attrs=None, date_format=None, time_format=None):
        if date_format:
            self.date_format = date_format
        if time_format:
            self.time_format = time_format
        split_widgets = (DateInput(attrs=attrs, format=self.date_format),
                   TimeInput(attrs=attrs, format=self.time_format))
        # Note that we're calling MultiWidget, not SplitDateTimeWidget, because
        # we want to define widgets.
        widgets.MultiWidget.__init__(self, split_widgets, attrs)

class SplitHiddenDateTimeWidget(DojoWidgetMixin, widgets.SplitHiddenDateTimeWidget):
    dojo_type = None
    
DateTimeInput = SplitDateTimeWidget

# ADDITIONAL DOJO SPECIFIC WIDGETS!
class EditorInput(Textarea):
    dojo_type = 'dijit.Editor'

class HorizontalSliderInput(TextInput):
    dojo_type = 'dijit.form.HorizontalSlider'
    
    def __init__(self, attrs=None):
        if dojo_config.version < '1.3.0':
            self.alt_require = 'dijit.form.Slider'
        super(HorizontalSliderInput, self).__init__(attrs)

class VerticalSliderInput(TextInput):
    dojo_type = 'dijit.form.VerticalSlider'
    
    def __init__(self, attrs=None):
        if dojo_config.version < '1.3.0':
            self.alt_require = 'dijit.form.Slider'
        super(VerticalSliderInput, self).__init__(attrs)

class ValidationTextInput(TextInput):
    dojo_type = 'dijit.form.ValidationTextBox'
    valid_extra_attrs = [
        'required',
        'help_text',
        'js_regex',
        'max_length',
    ]
    js_regex_func = None
    
    def render(self, name, value, attrs=None):
        if self.js_regex_func:
            attrs = self.build_attrs(attrs, regExpGen=self.js_regex_func)
        return super(ValidationTextInput, self).render(name, value, attrs)

class ValidationPasswordInput(PasswordInput):
    dojo_type = 'dijit.form.ValidationTextBox'
    valid_extra_attrs = [
        'required',
        'help_text',
        'js_regex',
        'max_length',
    ]

class EmailTextInput(ValidationTextInput):
    extra_dojo_require = [
        'dojox.validate.regexp'
    ]
    js_regex_func = "dojox.validate.regexp.emailAddress"
    
    def __init__(self, attrs=None):
        if dojo_config.version < '1.3.0':
            self.js_regex_func = 'dojox.regexp.emailAddress'
        super(EmailTextInput, self).__init__(attrs)
    
class IPAddressTextInput(ValidationTextInput):
    extra_dojo_require = [
        'dojox.validate.regexp'
    ]
    js_regex_func = "dojox.validate.regexp.ipAddress"
    
    def __init__(self, attrs=None):
        if dojo_config.version < '1.3.0':
            self.js_regex_func = 'dojox.regexp.ipAddress'
        super(IPAddressTextInput, self).__init__(attrs)
    
class URLTextInput(ValidationTextInput):
    extra_dojo_require = [
        'dojox.validate.regexp'
    ]
    js_regex_func = "dojox.validate.regexp.url"
    
    def __init__(self, attrs=None):
        if dojo_config.version < '1.3.0':
            self.js_regex_func = 'dojox.regexp.url'
        super(URLTextInput, self).__init__(attrs)
    
class NumberTextInput(TextInput):
    dojo_type = 'dijit.form.NumberTextBox'
    valid_extra_attrs = [
        'min_value',
        'max_value',
        'required',
        'help_text',
        'decimal_places',
    ]
    
class RangeBoundTextInput(NumberTextInput):
    dojo_type = 'dijit.form.RangeBoundTextBox'
    
class NumberSpinnerInput(NumberTextInput):
    dojo_type = 'dijit.form.NumberSpinner'

class RatingInput(TextInput):
    dojo_type = 'dojox.form.Rating'
    valid_extra_attrs = [
        'max_value',
    ]
    field_attr_map = {
        'max_value': 'numStars',
    }
    
    class Media:
        css = {
            'all': ('%(base_url)s/dojox/form/resources/Rating.css' % {
                'base_url':dojo_config.dojo_base_url
            },)
        }
