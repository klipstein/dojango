from django.forms.formsets import *
from django.forms.util import ValidationError
from django.utils.translation import ugettext as _
from django.forms.formsets import TOTAL_FORM_COUNT
from django.forms.formsets import INITIAL_FORM_COUNT
from django.forms.formsets import DELETION_FIELD_NAME
from django.forms.formsets import ORDERING_FIELD_NAME
from django.forms.formsets import formset_factory as django_formset_factory
from django.forms.forms import Form

from fields import IntegerField, BooleanField
from widgets import Media, HiddenInput

from django.forms.formsets import BaseFormSet

__all__ = ('BaseFormSet', 'all_valid')

class ManagementForm(Form):
    """
    Changed ManagementForm. It is using the dojango form fields.
    """
    def __init__(self, *args, **kwargs):
        self.base_fields[TOTAL_FORM_COUNT] = IntegerField(widget=HiddenInput)
        self.base_fields[INITIAL_FORM_COUNT] = IntegerField(widget=HiddenInput)
        Form.__init__(self, *args, **kwargs)

class BaseFormSet(BaseFormSet):
    """
    Overwritten BaseFormSet. Basically using the form extension of dojango.
    """
    def _dojango_management_form(self):
        """Attaching our own ManagementForm"""
        if self.data or self.files:
            form = ManagementForm(self.data, auto_id=self.auto_id, prefix=self.prefix)
            if not form.is_valid():
                raise ValidationError('ManagementForm data is missing or has been tampered with')
        else:
            is_dojo_1_0 = getattr(self, "_total_form_count", False)
            # this is for django versions before 1.1
            initial = {
                TOTAL_FORM_COUNT: is_dojo_1_0 and self._total_form_count or self.total_form_count(),
                INITIAL_FORM_COUNT: is_dojo_1_0 and self._initial_form_count or self.initial_form_count()
            }
            form = ManagementForm(auto_id=self.auto_id, prefix=self.prefix, initial=initial)
        return form
    dojango_management_form = property(_dojango_management_form)

    def __getattribute__(self, anatt):
        """This is the superhack for overwriting the management_form
        property of the super class using a newly defined ManagementForm.
        In Django this property should've be defined lazy:
        management_form = property(lambda self: self._management_form())
        """
        if anatt == 'management_form':
            anatt = "dojango_management_form"
        return super(BaseFormSet, self).__getattribute__(anatt)

    def add_fields(self, form, index):
        """Using the dojango form fields instead of the django ones"""
        is_dojo_1_0 = getattr(self, "_total_form_count", False)
        if self.can_order:
            # Only pre-fill the ordering field for initial forms.
            # before django 1.1 _total_form_count was used!
            if index < (is_dojo_1_0 and self._total_form_count or self.total_form_count()):
                form.fields[ORDERING_FIELD_NAME] = IntegerField(label=_(u'Order'), initial=index+1, required=False)
            else:
                form.fields[ORDERING_FIELD_NAME] = IntegerField(label=_(u'Order'), required=False)
        if self.can_delete:
            form.fields[DELETION_FIELD_NAME] = BooleanField(label=_(u'Delete'), required=False)
            
def formset_factory(*args, **kwargs):
    """Formset factory function that uses the dojango BaseFormSet"""
    if not kwargs.has_key("formset"):
        kwargs["formset"] = BaseFormSet
    return django_formset_factory(*args, **kwargs)
