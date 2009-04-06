from django.forms import widgets
from django.utils.encoding import StrAndUnicode, force_unicode
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from dojango.util.config import Config

from dojango.forms import collector

__all__ = [ 'Widget', 'FormValue', 'TextInput', 'PasswordTextInput',
            'ValidationTextInput', 'RangeBoundTextInput', 'HiddenInput', 'MultipleHiddenInput',
            'Textarea', 'CheckboxInput', 'Select', 'NullBooleanSelect', 'SelectMultiple', 'NumberSpinnerTextInput',
            'NumberSpinnerTextInput',
            'FileInput', 'EditorInput', 'HorizontalSliderInput',
            'VerticalSliderInput', 'DateInput', 'TimeInput',
            'DateTimeInput']

dojo_config = Config() # initialize the configuration

DEFAULT_FIELD_ATTR_MAP = { # these field attributes can be supported by the widgets
    'required':'required',
    'help_text':'promptMessage',
    'min_value':'constraints.min',
    'max_value':'constraints.max',
    'max_length':'maxlength',
    #'max_digits':'maxDigits',
    'decimal_places':'constraints.places',
    'js_regex':'regExp',
}

class Widget(widgets.Widget):
    dojo_type = 'dijit._Widget'

class FormValue(Widget):
    input_type = 'text'
    input_node_type = 'input'
    used_extra_attrs = []

    def __init__(self, attrs=None, **kwargs):
        extra_requires = getattr(self, "extra_dojo_require", [])
        for i in extra_requires:
            collector.add_module(i)
        super(FormValue, self).__init__(attrs)
        
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

    def render(self, name, value, attrs=None):
        # mixing in the extra_attrs of the field for validation purpose
        final_attrs = self.build_attrs(attrs, name=name, dojoType=self.dojo_type)
        extra_attrs = final_attrs.get("extra_attrs", False)
        if extra_attrs:
            for i in self.used_extra_attrs:
                field_val = extra_attrs.get(i, None)
                new_attr_name = DEFAULT_FIELD_ATTR_MAP.get(i, None)
                if field_val is not None and new_attr_name is not None:
                    attrs = self._mixin_attr(final_attrs, field_val, new_attr_name)
            del final_attrs["extra_attrs"]
        if value is None: value = ''
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(value)
        if self.input_type:
            # Only add the 'type' attribute if it's non-empty.
            final_attrs['type'] = force_unicode(self.input_type)
        collector.add_module(self.dojo_type)
        return mark_safe(u'<%s%s />' % (self.input_node_type, flatatt(final_attrs)))

class DateInput(FormValue):
    dojo_type = 'dijit.form.DateTextBox'
    used_extra_attrs = [
        'required',
        'help_text',
    ]

class TimeInput(FormValue):
    dojo_type = 'dijit.form.TimeTextBox'
    used_extra_attrs = [
        'required',
        'help_text',
    ]

class DateTimeInput(widgets.SplitDateTimeWidget):
    """
    DateTimeInput is using two input fields.
    """
    def __init__(self, attrs=None):
        split_widgets = [DateInput, TimeInput]
        # Note that we're calling MultiWidget, not SplitDateTimeWidget, because
        # we want to define widgets.
        widgets.MultiWidget.__init__(self, split_widgets, attrs)

class EditorInput(FormValue):
    input_node_type = 'div'
    input_type = 'text'
    dojo_type = 'dijit.Editor'

class HorizontalSliderInput(FormValue):
    dojo_type = 'dijit.form.HorizontalSlider'

class VerticalSliderInput(FormValue):
    dojo_type = 'dijit.form.VerticalSlider'

class TextInput(FormValue):
    dojo_type = 'dijit.form.TextBox'
    used_extra_attrs = [
        'max_length',
    ]
    
class PasswordTextInput(FormValue):
    dojo_type = 'dijit.form.TextBox'
    input_type = 'password'

    def __init__(self, attrs=None, render_value=True):
        super(PasswordTextInput, self).__init__(attrs)
        self.render_value = render_value

    def render(self, name, value, attrs=None):
        if not self.render_value: value=None
        return super(PasswordTextInput, self).render(name, value, attrs)

class ValidationTextInput(TextInput):
    dojo_type = 'dijit.form.ValidationTextBox'
    used_extra_attrs = [
        'required',
        'help_text',
        'js_regex',
        'max_length',
    ]

    def render(self, name, value, attrs=None):
        attrs = self.build_attrs(attrs, regExpGen=self.js_regex_func)
        return super(ValidationTextInput, self).render(name, value, attrs)

class EmailTextInput(ValidationTextInput):
    extra_dojo_require = [
        'dojox.validate.regexp'
    ]
    js_regex_func = "dojox.validate.regexp.emailAddress"
    
class IPAddressTextInput(ValidationTextInput):
    extra_dojo_require = [
        'dojox.validate.regexp'
    ]
    js_regex_func = "dojox.validate.regexp.ipAddress"
    
class URLTextInput(ValidationTextInput):
    extra_dojo_require = [
        'dojox.validate.regexp'
    ]
    js_regex_func = "dojox.validate.regexp.url"

class ValidationPasswordTextInput(ValidationTextInput):
    input_type = 'password'

    def __init__(self, attrs=None, render_value=True):
        super(PasswordTextInput, self).__init__(attrs)
        self.render_value = render_value

    def render(self, name, value, attrs=None):
        if not self.render_value: value=None
        return super(PasswordTextInput, self).render(name, value, attrs) 
    
class NumberTextInput(TextInput):
    dojo_type = 'dijit.form.NumberTextBox'
    used_extra_attrs = [
        'min_value',
        'max_value',
        'required',
        'help_text',
        'decimal_places',
    ]
    
class RangeBoundTextInput(NumberTextInput):
    dojo_type = 'dijit.form.RangeBoundTextBox'
    
class NumberSpinnerTextInput(NumberTextInput):
    dojo_type = 'dijit.form.NumberSpinner'

HiddenInput = widgets.HiddenInput
MultipleHiddenInput = widgets.MultipleHiddenInput

#TODO: mixin extra_attrs
class Textarea(widgets.Textarea):
    dojo_type = 'dijit.form.Textarea'
    def __init__(self, attrs=None):
        super(Textarea, self).__init__(attrs)
        self.attrs.update({'dojoType': self.dojo_type})

#TODO: mixin extra_attrs / replace collector-adding!
class CheckboxInput(FormValue, widgets.CheckboxInput):
    input_type = 'checkbox'
    dojo_type = 'dijit.form.CheckBox'

    def __init__(self, attrs=None, check_test=bool):
        widgets.CheckboxInput.__init__(self, attrs, check_test)
        collector.add_module(self.dojo_type)

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        try:
            result = self.check_test(value)
        except: # Silently catch exceptions
            result = False
        if result:
            final_attrs['checked'] = 'checked'
        return FormValue.render(self, name, value, final_attrs)

    def value_from_datadict(self, data, files, name):
        return widgets.CheckboxInput.value_from_datadict(self, data, files, name)

#TODO: mixin extra_attrs / replace collector-adding!
class Select(widgets.Select):
    dojo_type = 'dijit.form.FilteringSelect'
    def __init__(self, attrs=None, choices=()):
        super(Select, self).__init__(attrs, choices)
        self.attrs.update({'dojoType': self.dojo_type})
        collector.add_module(self.dojo_type)
#TODO: mixin extra_attrs / replace collector-adding!
class NullBooleanSelect(widgets.NullBooleanSelect):
    dojo_type = 'dijit.form.FilteringSelect'
    def __init__(self, attrs=None):
        super(NullBooleanSelect, self).__init__(attrs)
        self.attrs.update({'dojoType': self.dojo_type})
        collector.add_module(self.dojo_type)
#TODO: mixin extra_attrs / replace collector-adding!
class SelectMultiple(widgets.SelectMultiple):
    dojo_type = 'dijit.form.MultiSelect'
    def __init__(self, attrs=None, choices=()):
        super(SelectMultiple, self).__init__(attrs, choices)
        self.attrs.update({'dojoType': self.dojo_type})
        collector.add_module(self.dojo_type)

class FileInput(FormValue, widgets.FileInput):
    input_type = 'file'
    dojo_type = 'dojox.form.FileInput'
    class Media:
        css = {
            'all': ('%(base_url)s/dojox/form/resources/FileInput.css' % {
                'base_url':dojo_config.dojo_base_url
            },)
        }