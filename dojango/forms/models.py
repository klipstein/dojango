from django.forms import models
from django.forms.forms import get_declared_fields
from django.utils.text import capfirst

from django.db.models import fields

from dojango.forms.fields import *
from dojango.forms.widgets import Textarea, Select, SelectMultiple

__all__ = ['ModelChoiceField', 'ModelMultipleChoiceField', 'ModelForm',]

class ModelChoiceField(DojoFieldMixin, models.ModelChoiceField):
    """
    Overwritten 'ModelChoiceField' using the 'DojoFieldMixin' functonality.
    """
    widget = Select

class ModelMultipleChoiceField(DojoFieldMixin, models.ModelMultipleChoiceField):
    """
    Overwritten 'ModelMultipleChoiceField' using the 'DojoFieldMixin' functonality.
    """
    widget = SelectMultiple

# our customized model field => form field map
# here it is defined which form field is used by which model field, when creating a ModelForm
MODEL_TO_FORM_FIELD_MAP = (
    # (model_field, form_field, [optional widget])
    (fields.BooleanField, BooleanField),
    (fields.CharField, CharField),
    (fields.CommaSeparatedIntegerField, CharField),
    (fields.DateTimeField, DateTimeField), # must be in front of the DateField
    (fields.DateField, DateField),
    (fields.DecimalField, DecimalField),
    (fields.EmailField, EmailField),
    (fields.files.FileField, FileField),
    (fields.FilePathField, FilePathField),
    (fields.FloatField, FloatField),
    (fields.related.ForeignKey, ModelChoiceField),
    (fields.files.ImageField, ImageField),
    (fields.IntegerField, IntegerField),
    (fields.IPAddressField, IPAddressField),
    (fields.related.ManyToManyField, ModelMultipleChoiceField),
    (fields.NullBooleanField, CharField),
    (fields.PositiveIntegerField, IntegerField),
    (fields.PositiveSmallIntegerField, IntegerField),
    (fields.SlugField, SlugField),
    (fields.SmallIntegerField, IntegerField),
    (fields.TextField, CharField, Textarea),
    (fields.TimeField, TimeField),
    (fields.URLField, URLField),
    (fields.XMLField, CharField, Textarea),
)

def formfield_function(field):
    """
    Custom formfield function, so we can inject our own form fields. The 
    mapping of model fields to form fields is defined in 'MODEL_TO_FORM_FIELD_MAP'.
    It uses the default django mapping as fallback, if there is no match in our
    custom map.
    
    field -- a model field
    """
    for field_map in MODEL_TO_FORM_FIELD_MAP:
        if isinstance(field, field_map[0]):
            used_widget = None
            if field.choices:
                # the normal django field forms.TypedChoiceField is wired hard
                # within the original db/models/fields.py.
                # If we use our custom Select widget, we also have to pass in
                # some additional validation field attributes.
                used_widget = Select(attrs={
                    'extra_field_attrs':{
                        'required':not field.blank,
                        'help_text':field.help_text,
                    }
                })
            elif len(field_map) == 3:
                widget=field_map[2]
            if used_widget:
                return field.formfield(form_class=field_map[1], widget=used_widget)
            return field.formfield(form_class=field_map[1])
    # return the default formfield, if there is no equivalent
    return field.formfield()

class ModelFormMetaclass(models.ModelFormMetaclass):
    """
    Overwritten 'ModelFormMetaClass'. We attach our own formfield generation
    function.
    """
    def __new__(cls, name, bases, attrs):
        # this is how we can replace standard django form fields with dojo ones
        attrs["formfield_callback"] = formfield_function
        return super(ModelFormMetaclass, cls).__new__(cls, name, bases, attrs)

class ModelForm(models.ModelForm):
    """
    Overwritten 'ModelForm' using the metaclass defined above.
    """
    __metaclass__ = ModelFormMetaclass
