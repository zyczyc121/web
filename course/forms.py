from django import forms
from django.core.urlresolvers import reverse, reverse_lazy
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Fieldset, Field, MultiField, MultiWidgetField
from crispy_forms.bootstrap import FormActions
from ckeditor.widgets import CKEditorWidget
from ckeditor_uploader.widgets import CKEditorUploadingWidget
import competition.models


class StyleMixin:
    def __init__(self, *args, **kwargs):
        super(StyleMixin, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = ""
        self.helper.form_tag = False
        self.helper.label_class = "col-xs-3 col-md-3 col-lg-3"
        self.helper.field_class = "col-xs-9 col-md-9 col-lg-9"


class StyleHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(StyleHelper).__init__()
        self.form_tag = False
        self.label_class = "col-xs-3 col-md-3 col-lg-3"
        self.field_class = "col-xs-9 col-md-9 col-lg-9"


form_helper = FormHelper()
form_helper.form_tag = False
form_helper.label_class = "col-xs-3 col-md-3 col-lg-3"
form_helper.field_class = "col-xs-9 col-md-9 col-lg-9"


class CreateProjectForm(StyleMixin, forms.ModelForm):
    class Meta:
        model = competition.models.Competition
        fields = ['name', 'description', 'max_team_size', 'start_datetime', 'end_datetime', 'logo']

        labels = {
            'max_team_size': 'Maximum team size',
            'name': 'Assignment title',
            'logo': 'Logo (optional)'
        }


class EditDetailForm(StyleMixin, forms.Form):
    title = forms.CharField(max_length=50)
    content = forms.CharField(widget=CKEditorUploadingWidget())

    def __init__(self, *args, **kwargs):
        super(EditDetailForm, self).__init__(*args, **kwargs)
