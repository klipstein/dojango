import datetime

from django.forms import *
from django.utils import formats
from django.utils.encoding import StrAndUnicode, force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.utils import datetime_safe

from dojango.util import json_encode
from dojango.util.config import Config

from dojango.util import dojo_collector

__all__ = (
    'Media', 'MediaDefiningClass', # original django classes
    'DojoWidgetMixin', 'Input', 'Widget', 'TextInput', 'PasswordInput',
    'HiddenInput', 'MultipleHiddenInput', 'FileInput', 'Textarea',
    'DateInput', 'DateTimeInput', 'TimeInput', 'CheckboxInput', 'Select',
    'NullBooleanSelect', 'SelectMultiple', 'RadioInput', 'RadioFieldRenderer',
    'RadioSelect', 'CheckboxSelectMultiple', 'MultiWidget', 'SplitDateTimeWidget',
    'SplitHiddenDateTimeWidget', 'SimpleTextarea', 'EditorInput', 'HorizontalSliderInput',
    'VerticalSliderInput', 'ValidationTextInput', 'ValidationPasswordInput',
    'EmailTextInput', 'IPAddressTextInput', 'URLTextInput', 'NumberTextInput',
    'RangeBoundTextInput', 'NumberSpinnerInput', 'RatingInput', 'DateInputAnim',
    'DropDownSelect', 'CheckedMultiSelect', 'FilteringSelect', 'ComboBox',
    'ComboBoxStore', 'FilteringSelectStore', 'ListInput',
)

dojo_config = Config() # initialize the configuration

class DojoWidgetMixin:
    """A helper mixin, that is used by every custom dojo widget.
    Some dojo widgets can utilize the validation information of a field and here
    we mixin those attributes into the widget. Field attributes that are listed
    in the 'valid_extra_attrs' will be mixed into the attributes of a widget.

    The 'default_field_attr_map' property contains the default mapping of field
    attributes to dojo widget attributes.

    This mixin also takes care passing the required dojo modules to the collector.
    'dojo_type' defines the used dojo module type of this widget and adds this
    module to the collector, if no 'alt_require' property is defined. When
    'alt_require' is set, this module will be passed to the collector. By using
    'extra_dojo_require' it is possible to pass additional dojo modules to the
    collector.
    """
    dojo_type = None # this is the dojoType definition of the widget. also used for generating the dojo.require call
    alt_require = None # alternative dojo.require call (not using the dojo_type)
    extra_dojo_require = [] # these dojo modules also needs to be loaded for this widget

    default_field_attr_map = { # the default map for mapping field attributes to dojo attributes
        'required':'required',
        'help_text':'promptMessage',
        'min_value':'constraints.min',
        'max_value':'constraints.max',
        'max_length':'maxLength',
        'max_digits':'maxLength',
        'decimal_places':'constraints.places',
        'js_regex':'regExp',
        'multiple':'multiple',
    }
    field_attr_map = {} # used for overwriting the default attr-map
    valid_extra_attrs = [] # these field_attributes are valid for the current widget

    def _mixin_attr(self, attrs, key, value):
        """Mixes in the passed key/value into the passed attrs and returns that
        extended attrs dictionary.

        A 'key', that is separated by a dot, e.g. 'constraints.min', will be
        added as:

        {'constraints':{'min':value}}
        """
        dojo_field_attr = key.split(".")
        inner_dict = attrs
        len_fields = len(dojo_field_attr)
        count = 0
        for i in dojo_field_attr:
            count = count+1
            if count == len_fields and inner_dict.get(i, None) is None:
                if isinstance(value, datetime.datetime):
                    if isinstance(self, TimeInput):
                        value = value.strftime('T%H:%M:%S')
                    if isinstance(self, DateInput):
                        value = value.strftime('%Y-%m-%d')
                    value = str(value).replace(' ', 'T') # see dojo.date.stamp
                if isinstance(value, datetime.date):
                    value = str(value)
                if isinstance(value, datetime.time):
                    value = "T" + str(value) # see dojo.date.stamp
                inner_dict[i] = value
            elif not inner_dict.has_key(i):
                inner_dict[i] = {}
            inner_dict = inner_dict[i]
        return attrs

    def build_attrs(self, extra_attrs=None, **kwargs):
        """Overwritten helper function for building an attribute dictionary.
        This helper also takes care passing the used dojo modules to the
        collector. Furthermore it mixes in the used field attributes into the
        attributes of this widget.
        """
        # gathering all widget attributes
        attrs = dict(self.attrs, **kwargs)
        field_attr = self.default_field_attr_map.copy() # use a copy of that object. otherwise changed field_attr_map would overwrite the default-map for all widgets!
        field_attr.update(self.field_attr_map) # the field-attribute-mapping can be customzied
        if extra_attrs:
            attrs.update(extra_attrs)
        # assigning dojoType to our widget
        dojo_type = getattr(self, "dojo_type", False)
        if dojo_type:
            attrs["dojoType"] = dojo_type # add the dojoType attribute

        # fill the global collector object
        if getattr(self, "alt_require", False):
            dojo_collector.add_module(self.alt_require)
        elif dojo_type:
            dojo_collector.add_module(self.dojo_type)
        extra_requires = getattr(self, "extra_dojo_require", [])
        for i in extra_requires:
            dojo_collector.add_module(i)

        # mixin those additional field attrs, that are valid for this widget
        extra_field_attrs = attrs.get("extra_field_attrs", False)
        if extra_field_attrs:
            for i in self.valid_extra_attrs:
                field_val = extra_field_attrs.get(i, None)
                new_attr_name = field_attr.get(i, None)
                if field_val is not None and new_attr_name is not None:
                    attrs = self._mixin_attr(attrs, new_attr_name, field_val)
            del attrs["extra_field_attrs"]

        # now encode several attributes, e.g. False = false, True = true
        for i in attrs:
            if isinstance(attrs[i], bool):
                attrs[i] = json_encode(attrs[i])
        return attrs

#############################################
# ALL OVERWRITTEN DEFAULT DJANGO WIDGETS
#############################################

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
    dojo_type = 'dijit.form.TextBox' # otherwise dijit.form.Form can't get its values

class MultipleHiddenInput(DojoWidgetMixin, widgets.MultipleHiddenInput):
    dojo_type = 'dijit.form.TextBox' # otherwise dijit.form.Form can't get its values

class FileInput(DojoWidgetMixin, widgets.FileInput):
    dojo_type = 'dojox.form.FileInput'
    class Media:
        css = {
            'all': ('%(base_url)s/dojox/form/resources/FileInput.css' % {
                'base_url':dojo_config.dojo_base_url
            },)
        }

class Textarea(DojoWidgetMixin, widgets.Textarea):
    """Auto resizing textarea"""
    dojo_type = 'dijit.form.Textarea'
    valid_extra_attrs = [
        'max_length'
    ]

if DateInput:
    class DateInput(DojoWidgetMixin, widgets.DateInput):
        dojo_type = 'dijit.form.DateTextBox'
        valid_extra_attrs = [
            'required',
            'help_text',
            'min_value',
            'max_value',
        ]
else:  # fallback for older django versions
    class DateInput(TextInput):
        """Copy of the implementation in Django 1.1. Before this widget did not exists."""
        dojo_type = 'dijit.form.DateTextBox'
        valid_extra_attrs = [
            'required',
            'help_text',
            'min_value',
            'max_value',
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

if TimeInput:
    class TimeInput(DojoWidgetMixin, widgets.TimeInput):
        dojo_type = 'dijit.form.TimeTextBox'
        valid_extra_attrs = [
            'required',
            'help_text',
            'min_value',
            'max_value',
        ]
        format = "T%H:%M:%S" # special for dojo: 'T12:12:33'
        
        def __init__(self, attrs=None, format=None):
            # always passing the dojo time format
            super(TimeInput, self).__init__(attrs, format=self.format)
        
        def _has_changed(self, initial, data):
            try:
                input_format = self.format
                initial = datetime.time(*time.strptime(initial, input_format)[3:6])
            except (TypeError, ValueError):
                pass
            return super(TimeInput, self)._has_changed(self._format_value(initial), data)

else: # fallback for older django versions
    class TimeInput(TextInput):
        """Copy of the implementation in Django 1.1. Before this widget did not exists."""
        dojo_type = 'dijit.form.TimeTextBox'
        valid_extra_attrs = [
            'required',
            'help_text',
            'min_value',
            'max_value',
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
    dojo_type = dojo_config.version < '1.4' and 'dijit.form.FilteringSelect' or 'dijit.form.Select'
    valid_extra_attrs = dojo_config.version < '1.4' and \
        ['required', 'help_text',] or \
        ['required',]

class NullBooleanSelect(DojoWidgetMixin, widgets.NullBooleanSelect):
    dojo_type = dojo_config.version < '1.4' and 'dijit.form.FilteringSelect' or 'dijit.form.Select'
    valid_extra_attrs = dojo_config.version < '1.4' and \
        ['required', 'help_text',] or \
        ['required',]

class SelectMultiple(DojoWidgetMixin, widgets.SelectMultiple):
    dojo_type = 'dijit.form.MultiSelect'

RadioInput = widgets.RadioInput
RadioFieldRenderer = widgets.RadioFieldRenderer

class RadioSelect(DojoWidgetMixin, widgets.RadioSelect):
    dojo_type = 'dijit.form.RadioButton'

    def __init__(self, *args, **kwargs):
        if dojo_config.version < '1.3':
            self.alt_require = 'dijit.form.CheckBox'
        super(RadioSelect, self).__init__(*args, **kwargs)

class CheckboxSelectMultiple(DojoWidgetMixin, widgets.CheckboxSelectMultiple):
    dojo_type = 'dijit.form.CheckBox'

class MultiWidget(DojoWidgetMixin, widgets.MultiWidget):
    dojo_type = None

class SplitDateTimeWidget(widgets.SplitDateTimeWidget):
    "DateTimeInput is using two input fields."
    try:
        # for older django versions 
        date_format = DateInput.format
        time_format = TimeInput.format
    except AttributeError:
        date_format = None
        time_format = None


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
    dojo_type = "dijit.form.TextBox"

DateTimeInput = SplitDateTimeWidget

#############################################
# MORE ENHANCED DJANGO/DOJO WIDGETS
#############################################

class SimpleTextarea(Textarea):
    """No autoexpanding textarea"""
    dojo_type = "dijit.form.SimpleTextarea"

class EditorInput(Textarea):
    dojo_type = 'dijit.Editor'

    def render(self, name, value, attrs=None):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        # dijit.Editor must be rendered in a div (see dijit/_editor/RichText.js)
        return mark_safe(u'<div%s>%s</div>' % (flatatt(final_attrs),
                force_unicode(value))) # we don't escape the value for the editor

class HorizontalSliderInput(TextInput):
    dojo_type = 'dijit.form.HorizontalSlider'
    valid_extra_attrs = [
        'max_value',
        'min_value',
    ]
    field_attr_map = {
        'max_value': 'maximum',
        'min_value': 'minimum',
    }

    def __init__(self, attrs=None):
        if dojo_config.version < '1.3':
            self.alt_require = 'dijit.form.Slider'
        super(HorizontalSliderInput, self).__init__(attrs)

class VerticalSliderInput(HorizontalSliderInput):
    dojo_type = 'dijit.form.VerticalSlider'

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
        if dojo_config.version < '1.3':
            self.js_regex_func = 'dojox.regexp.emailAddress'
        super(EmailTextInput, self).__init__(attrs)

class IPAddressTextInput(ValidationTextInput):
    extra_dojo_require = [
        'dojox.validate.regexp'
    ]
    js_regex_func = "dojox.validate.regexp.ipAddress"

    def __init__(self, attrs=None):
        if dojo_config.version < '1.3':
            self.js_regex_func = 'dojox.regexp.ipAddress'
        super(IPAddressTextInput, self).__init__(attrs)

class URLTextInput(ValidationTextInput):
    extra_dojo_require = [
        'dojox.validate.regexp'
    ]
    js_regex_func = "dojox.validate.regexp.url"

    def __init__(self, attrs=None):
        if dojo_config.version < '1.3':
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
        'max_digits',
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

class DateInputAnim(DateInput):
    dojo_type = 'dojox.form.DateTextBox'
    class Media:
        css = {
            'all': ('%(base_url)s/dojox/widget/Calendar/Calendar.css' % {
                'base_url':dojo_config.dojo_base_url
            },)
        }

class DropDownSelect(Select):
    dojo_type = 'dojox.form.DropDownSelect'
    valid_extra_attrs = []
    class Media:
        css = {
            'all': ('%(base_url)s/dojox/form/resources/DropDownSelect.css' % {
                'base_url':dojo_config.dojo_base_url
            },)
        }

class CheckedMultiSelect(SelectMultiple):
    dojo_type = 'dojox.form.CheckedMultiSelect'
    valid_extra_attrs = []
    # TODO: fix attribute multiple=multiple 
    # seems there is a dependency in dojox.form.CheckedMultiSelect for dijit.form.MultiSelect,
    # but CheckedMultiSelect is not extending that

    class Media:
        css = {
            'all': ('%(base_url)s/dojox/form/resources/CheckedMultiSelect.css' % {
                'base_url':dojo_config.dojo_base_url
            },)
        }

class ComboBox(DojoWidgetMixin, widgets.Select):
    """Nearly the same as FilteringSelect, but ignoring the option value."""
    dojo_type = 'dijit.form.ComboBox'
    valid_extra_attrs = [
        'required', 
        'help_text',
    ]

class FilteringSelect(ComboBox):
    dojo_type = 'dijit.form.FilteringSelect'

class ComboBoxStore(TextInput):
    """A combobox that is receiving data from a given dojo data url.
    As default dojo.data.ItemFileReadStore is used. You can overwrite
    that behaviour by passing a different store name 
    (e.g. dojox.data.QueryReadStore).
    Usage:
        ComboBoxStore("/dojo-data-store-url/")
    """
    dojo_type = 'dijit.form.ComboBox'
    valid_extra_attrs = [
        'required', 
        'help_text',
    ]
    store = 'dojo.data.ItemFileReadStore'
    store_attrs = {}
    url = None
    
    def __init__(self, url, attrs=None, store=None, store_attrs={}):
        self.url = url
        if store:
            self.store = store
        if store_attrs:
            self.store_attrs = store_attrs
        self.extra_dojo_require.append(self.store)
        super(ComboBoxStore, self).__init__(attrs)
    
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        store_id = self.get_store_id(getattr(attrs, "id", None), name)
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name, store=store_id)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(self._format_value(value))
        self.store_attrs.update({
            'dojoType': self.store,
            'url': self.url,
            'jsId':store_id
        })
        # TODO: convert store attributes to valid js-format (False => false, dict => {}, array = [])
        store_node = '<div%s></div>' % flatatt(self.store_attrs)
        return mark_safe(u'%s<input%s />' % (store_node, flatatt(final_attrs)))

    def get_store_id(self, id, name):
        return "_store_" + (id and id or name)

class FilteringSelectStore(ComboBoxStore):
    dojo_type = 'dijit.form.FilteringSelect'
    
class ListInput(DojoWidgetMixin, widgets.TextInput):
    dojo_type = 'dojox.form.ListInput'
    class Media:
        css = {
            'all': ('%(base_url)s/dojox/form/resources/ListInput.css' % {
                'base_url':dojo_config.dojo_base_url
            },)
        }

# THE RANGE SLIDER NEEDS A DIFFERENT REPRESENTATION WITHIN HTML
# SOMETHING LIKE:
# <div dojoType="dojox.form.RangeSlider"><input value="5"/><input value="10"/></div>
'''class HorizontalRangeSlider(HorizontalSliderInput):
    """This just can be used with a comma-separated-value like: 20,40"""
    dojo_type = 'dojox.form.HorizontalRangeSlider'
    alt_require = 'dojox.form.RangeSlider'

    class Media:
        css = {
            'all': ('%(base_url)s/dojox/form/resources/RangeSlider.css' % {
                'base_url':dojo_config.dojo_base_url
            },)
        }
'''
# TODO: implement
# dojox.form.RangeSlider
# dojox.form.MultiComboBox
# dojox.form.FileUploader
