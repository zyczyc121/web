from django import forms
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from .models import UserInfo
from captcha.fields import CaptchaField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Fieldset, Field, MultiField, MultiWidgetField
from crispy_forms.bootstrap import FormActions
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=20, validators=[
        RegexValidator(r'^[a-zA-Z][a-zA-Z0-9_]+$',
                       message="Username can contain only numbers, letters and underscores")],
                       required=True)
    display_name = forms.CharField(max_length=30, label="Display Name",
                                   validators=[RegexValidator(r"^(\w|\d|[ ,_'])+$")], required=True)
    real_name = forms.CharField(max_length=50, label="Real Name",
                                   validators=[RegexValidator(r"^(\w|\d|[ ,_'])+$")], required=True)

    organization = forms.CharField(max_length=500, label="Organization",
                                   validators=[RegexValidator(r"^(\w|\d|[ ,_'])+$")], required=True)

    email = forms.EmailField(required=True)

    password = forms.CharField(widget=forms.PasswordInput, max_length=20, min_length=7, required=True)
    password_confirm = forms.CharField(label="Confirm Password",
                                       widget=forms.PasswordInput, max_length=20, min_length=7, required=True)

    captcha = CaptchaField(label="Validation Code")

    receive_update = forms.BooleanField(initial=True, label="Receive updates", required=False,
                                        widget=forms.CheckboxInput())

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = reverse('user:register')
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-md-4"
        self.helper.field_class = "col-md-7"
        # self.helper.
        self.helper.layout = Layout(
            Field('username', placeholder="The user name you hope to login"),
            Field('display_name', placeholder="Your real name displayed to others"),
            Field('real_name', placeholder="For authentication, won't displayed"),
            Field('organization', placeholder="For authentication"),
            Field('email', placeholder="We'll send an validation email later"),
            Field('password', placeholder="At least 7 characters"),
            Field('password_confirm', placeholder="Type the password again"),
            Field('captcha', placeholder="Captcha"),
            Field('receive_update'),
            FormActions(Submit('submit', _('Sign Up')))
        )

    def clean(self):
        errors = []
        password_1 = self.cleaned_data.get('password')
        password_2 = self.cleaned_data.get('password_confirm')

        if password_1 and password_2 != password_1:
            errors.append(forms.ValidationError(_("Password doesn't match!")))

        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')

        if username and User.objects.filter(username=username).exists():
            errors.append(forms.ValidationError(_("Username has been used!")))
        if email and User.objects.filter(email=email).exists():
            errors.append(forms.ValidationError(_("Email address has been used!")))

        if len(errors) > 0:
            raise forms.ValidationError(errors)

        return self.cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField(max_length=50, label='', widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(max_length=20, label='', widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    remember = forms.BooleanField(label="Remember Me", initial=True, required=False, widget=forms.CheckboxInput())
    next = forms.CharField(max_length=200, widget=forms.HiddenInput, required=False, initial='')

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.add_input(Submit('submit', _('Login')))


class ProfileEditForm(forms.ModelForm):
    interests = forms.CharField(widget=forms.HiddenInput, required=True)
    tools = forms.CharField(widget=forms.HiddenInput, required=True)

    interests_edit = forms.CharField(widget=forms.Textarea(attrs={'rows': 1}), required=False)
    tools_edit = forms.CharField(widget=forms.Textarea(attrs={'rows': 1}), required=False)

    class Meta:
        model = UserInfo
        fields = ['organization', 'bio', 'personal_tag', 'city', 'province', 'country',
                  'github_account', 'linkedin_url', 'twitter_account']

    def __init__(self, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_id = 'id-profile-edit-form'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('user:edit_profile')
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Fieldset(
                _('Organization'),
                Field('organization', placeholder=_("Name of your school department, company, or something else")),
            ),
            Fieldset(
                _('Bio'),
                Field('personal_tag', placeholder=_("Enter personal tagline here")),
                Field('bio', placeholder=_("Bio here")),
            ),
            Fieldset(
                _('Location'),
                Field('city', placeholder=_("City of residence")),
                Field('province', placeholder=_("State/Province")),
                Field('country', Placeholder=_("Country of residence"))
            ),
            Fieldset(
                _('Social'),
                Field('github_account', placeholder=_("Your github account")),
                Field('linkedin_url', placeholder=_("Your linkedin profile url")),
                Field('twitter_account', placeholder=_("Your twitter account"))
            ),
            Fieldset(
                _('Skills(Required)'),
                Field('interests_edit',
                      placeholder=_("Machine learning techniques you are familiar with. Split with ','")),
                Field('tools_edit', placeholder=_("Tools you are familiar with. Split with ','")),
                Field('tools'),
                Field('interests'),
            ),
            FormActions(Submit('submit', _('Save changes')))
        )


class ActivateForm(forms.Form):
    key = forms.CharField(max_length=128, widget=forms.HiddenInput)
    captcha = CaptchaField(label="Validation Code")

    def __init__(self, *args, **kwargs):
        super(ActivateForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-activate-form'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('user:activate')
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-md-3"
        self.helper.field_class = "col-md-7"

        self.helper.layout = Layout(
            Field('captcha'),
            Field('key'),
            FormActions(Submit('submit', _('Activate')))
        )


class ForgetPasswordForm(forms.Form):
    email = forms.EmailField(label="Email")
    captcha = CaptchaField(label="Validation Code")

    def __init__(self, *args, **kwargs):
        super(ForgetPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'id-forgot-password-form'
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-md-3"
        self.helper.field_class = "col-md-7"
        self.helper.form_method = 'post'

        self.helper.form_action = reverse('user:forget_password')

        self.helper.layout = Layout(
            Field('email', placeholder=_("The email address used in registration")),
            Field('captcha'),
            FormActions(
                Submit('submit', _('Reset Password'))
            )
        )


class ResetPasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, max_length=20, )
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password", max_length=20)
    key = forms.CharField(widget=forms.HiddenInput, max_length=128)
    captcha = CaptchaField(label="Validation Code")

    def __init__(self, *args, **kwargs):
        super(ResetPasswordForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-md-4"
        self.helper.field_class = "col-md-7"
        self.helper.form_id = 'id-reset-password-form'
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('user:reset_password')

        self.helper.layout = Layout(
            Field("password", placeholder=_("New password")),
            Field("password_confirm", placeholder=_("Type new password again")),
            Field("key"),
            Field('captcha'),
            FormActions(
                Submit('submit', _('Reset'))
            )
        )

    def clean(self):
        errors = []
        password_1 = self.cleaned_data.get('password')
        password_2 = self.cleaned_data.get('password_confirm')

        if password_1 and password_2 != password_1:
            errors.append(forms.ValidationError(_("Password doesn't match!")))
        if len(errors) > 0:
            raise forms.ValidationError(errors)
