from django.forms import models
from django.forms.forms import get_declared_fields
from django.utils.text import capfirst

from django.db.models import fields

from dojango.forms.fields import *
from dojango.forms.widgets import Textarea, Select, SelectMultiple

__all__ = ['ModelForm', 'ModelChoiceField', 'ModelMultipleChoiceField',]

def get_formfield(field, form_class=CharField, **kwargs):
    defaults = {'required': not field.blank, 'label': capfirst(field.verbose_name), 'help_text': field.help_text}
    if field.choices:
        defaults['widget'] = Select(choices=field.get_choices(include_blank=field.blank or not (field.has_default() or 'initial' in kwargs)))
    if field.has_default():
        defaults['initial'] = field.get_default()
    defaults.update(kwargs)
    return form_class(**defaults)

def formfield_function(field):
    if isinstance(field, fields.CharField):
        return get_formfield(field, CharField)
    elif isinstance(field, fields.IntegerField):
        return field.formfield(form_class=IntegerField)
    elif isinstance(field, fields.BooleanField):
        return field.formfield(form_class=BooleanField)
    elif isinstance(field, fields.files.FileField):
        return field.formfield(form_class=FileField)
    elif isinstance(field, fields.files.ImageField):
        return field.formfield(form_class=FileField)
    elif isinstance(field, fields.DateTimeField):
        return field.formfield(form_class=DateTimeField)
    elif isinstance(field, fields.DateField):
        return field.formfield(form_class=DateField)
    elif isinstance(field, fields.TimeField):
        return field.formfield(form_class=TimeField)
    # return the default formfield, if there is no equivalent
    return field.formfield()

class ModelFormMetaclass(models.ModelFormMetaclass):
    def __new__(cls, name, bases, attrs):
        # this is how we can replace standard django form fields with dojo ones
        attrs["formfield_callback"] = formfield_function
        return super(ModelFormMetaclass, cls).__new__(cls, name, bases, attrs)

class ModelForm(models.ModelForm):
    __metaclass__ = ModelFormMetaclass
    
class ModelChoiceField(DojoFieldMixin, models.ModelChoiceField):
    widget = Select

class ModelMultipleChoiceField(DojoFieldMixin, models.ModelMultipleChoiceField):
    widget = SelectMultiple

'''
AutoField     Not represented in the form
BooleanField     BooleanField
CharField     with max_length set to the model field's max_length
CommaSeparatedIntegerField     CharField
DateField     DateField
DateTimeField     DateTimeField
DecimalField     DecimalField
EmailField     EmailField
FileField     FileField
FilePathField     CharField
FloatField     FloatField
ForeignKey     ModelChoiceField (see below)
ImageField     ImageField
IntegerField     IntegerField
IPAddressField     IPAddressField
ManyToManyField     ModelMultipleChoiceField (see below)
NullBooleanField     CharField
PhoneNumberField     USPhoneNumberField (from django.contrib.localflavor.us)
PositiveIntegerField     IntegerField
PositiveSmallIntegerField     IntegerField
SlugField     SlugField
SmallIntegerField     IntegerField
TextField     CharField with widget=Textarea
TimeField     TimeField
URLField     URLField with verify_exists set to the model field's verify_exists
XMLField     CharField with widget=Textarea
'''