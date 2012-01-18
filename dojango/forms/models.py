from django.forms import *
from django.forms.models import BaseModelFormSet
from django.forms.models import BaseInlineFormSet
from django.forms.models import ModelChoiceIterator
from django.forms.models import InlineForeignKeyHiddenInput, InlineForeignKeyField

from django.utils.text import capfirst

from formsets import BaseFormSet

from django.db.models import fields

from dojango.forms.fields import *
from dojango.forms.widgets import DojoWidgetMixin, Textarea, Select, SelectMultiple, HiddenInput

__all__ = (
    'ModelForm', 'BaseModelForm', 'model_to_dict', 'fields_for_model',
    'save_instance', 'ModelChoiceField', 'ModelMultipleChoiceField',
)
    
class ModelChoiceField(DojoFieldMixin, models.ModelChoiceField):
    """
    Overwritten 'ModelChoiceField' using the 'DojoFieldMixin' functionality.
    """
    widget = Select

class ModelMultipleChoiceField(DojoFieldMixin, models.ModelMultipleChoiceField):
    """
    Overwritten 'ModelMultipleChoiceField' using the 'DojoFieldMixin' functonality.
    """
    widget = SelectMultiple

# Fields #####################################################################

class InlineForeignKeyHiddenInput(DojoWidgetMixin, InlineForeignKeyHiddenInput):
    """
    Overwritten InlineForeignKeyHiddenInput to use the dojango widget mixin
    """
    dojo_type = 'dijit.form.TextBox' # otherwise dijit.form.Form can't get its values

class InlineForeignKeyField(DojoFieldMixin, InlineForeignKeyField, Field):
    """
    Overwritten InlineForeignKeyField to use the dojango field mixin and passing
    the dojango InlineForeignKeyHiddenInput as widget.
    """
    def __init__(self, parent_instance, *args, **kwargs):
        self.parent_instance = parent_instance
        self.pk_field = kwargs.pop("pk_field", False)
        self.to_field = kwargs.pop("to_field", None)
        if self.parent_instance is not None:
            if self.to_field:
                kwargs["initial"] = getattr(self.parent_instance, self.to_field)
            else:
                kwargs["initial"] = self.parent_instance.pk

        kwargs["required"] = False
        kwargs["widget"] = InlineForeignKeyHiddenInput
        # don't call the the superclass of this one. Use the superclass of the 
        # normal django InlineForeignKeyField
        Field.__init__(self, *args, **kwargs)

# our customized model field => form field map
# here it is defined which form field is used by which model field, when creating a ModelForm
MODEL_TO_FORM_FIELD_MAP = (
    # (model_field, form_field, [optional widget])
    # the order of these fields is very important for inherited model fields
    # e.g. the CharField must be checked at last, because several other
    # fields are a subclass of it.
    (fields.CommaSeparatedIntegerField, CharField),
    (fields.DateTimeField, DateTimeField), # must be in front of the DateField
    (fields.DateField, DateField),
    (fields.DecimalField, DecimalField),
    (fields.EmailField, EmailField),
    (fields.FilePathField, FilePathField),
    (fields.FloatField, FloatField),
    (fields.related.ForeignKey, ModelChoiceField),
    (fields.files.ImageField, ImageField),
    (fields.files.FileField, FileField),
    (fields.IPAddressField, IPAddressField),
    (fields.related.ManyToManyField, ModelMultipleChoiceField),
    (fields.NullBooleanField, CharField),
    (fields.BooleanField, BooleanField),
    (fields.PositiveSmallIntegerField, IntegerField),
    (fields.PositiveIntegerField, IntegerField),
    (fields.SlugField, SlugField),
    (fields.SmallIntegerField, IntegerField),
    (fields.IntegerField, IntegerField),
    (fields.TimeField, TimeField),
    (fields.URLField, URLField),
    (fields.TextField, CharField, Textarea),
    (fields.CharField, CharField),
)

def formfield_function(field, **kwargs):
    """
    Custom formfield function, so we can inject our own form fields. The 
    mapping of model fields to form fields is defined in 'MODEL_TO_FORM_FIELD_MAP'.
    It uses the default django mapping as fallback, if there is no match in our
    custom map.
    
    field -- a model field
    """
    for field_map in MODEL_TO_FORM_FIELD_MAP:
        if isinstance(field, field_map[0]):
            defaults = {}
            if field.choices:
                # the normal django field forms.TypedChoiceField is wired hard
                # within the original db/models/fields.py.
                # If we use our custom Select widget, we also have to pass in
                # some additional validation field attributes.
                defaults['widget'] = Select(attrs={
                    'extra_field_attrs':{
                        'required':not field.blank,
                        'help_text':field.help_text,
                    }
                })
            elif len(field_map) == 3:
                defaults['widget']=field_map[2]
            defaults.update(kwargs)
            return field.formfield(form_class=field_map[1], **defaults)
    # return the default formfield, if there is no equivalent
    return field.formfield(**kwargs)

# ModelForms #################################################################

def fields_for_model(*args, **kwargs):
    """Changed fields_for_model function, where we use our own formfield_callback"""
    kwargs["formfield_callback"] = formfield_function
    return models.fields_for_model(*args, **kwargs)

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

def modelform_factory(*args, **kwargs):
    """Changed modelform_factory function, where we use our own formfield_callback"""
    kwargs["formfield_callback"] = formfield_function
    kwargs["form"] = ModelForm
    return models.modelform_factory(*args, **kwargs)

# ModelFormSets ##############################################################

class BaseModelFormSet(BaseModelFormSet, BaseFormSet):
    
    def add_fields(self, form, index):
        """Overwritten BaseModelFormSet using the dojango BaseFormSet and
        the ModelChoiceField. 
        NOTE: This method was copied from django 1.3 beta 1"""
        from django.db.models import AutoField, OneToOneField, ForeignKey
        self._pk_field = pk = self.model._meta.pk
        def pk_is_not_editable(pk):
            return ((not pk.editable) or (pk.auto_created or isinstance(pk, AutoField))
                or (pk.rel and pk.rel.parent_link and pk_is_not_editable(pk.rel.to._meta.pk)))
        if pk_is_not_editable(pk) or pk.name not in form.fields:
            if form.is_bound:
                pk_value = form.instance.pk
            else:
                try:
                    if index is not None:
                        pk_value = self.get_queryset()[index].pk
                    else:
                        pk_value = None
                except IndexError:
                    pk_value = None
            if isinstance(pk, OneToOneField) or isinstance(pk, ForeignKey):
                qs = pk.rel.to._default_manager.get_query_set()
            else:
                qs = self.model._default_manager.get_query_set()
            qs = qs.using(form.instance._state.db)
            form.fields[self._pk_field.name] = ModelChoiceField(qs, initial=pk_value, required=False, widget=HiddenInput)
        BaseFormSet.add_fields(self, form, index)

def modelformset_factory(*args, **kwargs):
    """Changed modelformset_factory function, where we use our own formfield_callback"""
    kwargs["formfield_callback"] = kwargs.get("formfield_callback", formfield_function)
    kwargs["formset"] = kwargs.get("formset", BaseModelFormSet)
    return models.modelformset_factory(*args, **kwargs)

# InlineFormSets #############################################################

class BaseInlineFormSet(BaseInlineFormSet, BaseModelFormSet):
    """Overwritten BaseInlineFormSet using the dojango InlineForeignKeyFields.
    NOTE: This method was copied from django 1.1"""
    def add_fields(self, form, index):
        super(BaseInlineFormSet, self).add_fields(form, index)
        if self._pk_field == self.fk:
            form.fields[self._pk_field.name] = InlineForeignKeyField(self.instance, pk_field=True)
        else:
            kwargs = {
                'label': getattr(form.fields.get(self.fk.name), 'label', capfirst(self.fk.verbose_name))
            }
            if self.fk.rel.field_name != self.fk.rel.to._meta.pk.name:
                kwargs['to_field'] = self.fk.rel.field_name
            form.fields[self.fk.name] = InlineForeignKeyField(self.instance, **kwargs)
            
def inlineformset_factory(*args, **kwargs):
    """Changed inlineformset_factory function, where we use our own formfield_callback"""
    kwargs["formfield_callback"] = kwargs.get("formfield_callback", formfield_function)
    kwargs["formset"] = kwargs.get("formset", BaseInlineFormSet)
    return models.inlineformset_factory(*args, **kwargs)
