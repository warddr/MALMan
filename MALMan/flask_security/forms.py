# -*- coding: utf-8 -*-
"""
    flask.ext.security.forms
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Flask-Security forms module

    :copyright: (c) 2012 by Matt Wright.
    :license: MIT, see LICENSE for more details.
"""

from flask import request, current_app
from flask.ext.wtf import Form as BaseForm, TextField, PasswordField, \
     SubmitField, HiddenField, Required, BooleanField, EqualTo, Email, \
     ValidationError, Length
from werkzeug.local import LocalProxy

from flask.ext.wtf import validators


from .confirmable import requires_confirmation
from .utils import verify_password, get_message

# Convenient reference
_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)

email_required = Required(message='Email not provided')

email_validator = Email(message='Invalid email address')

password_required = Required(message="Password not provided")


def unique_user_email(form, field):
    if _datastore.find_user(email=field.data) is not None:
        raise ValidationError(field.data +
                              ' is already associated with an account')


def valid_user_email(form, field):
    form.user = _datastore.find_user(email=field.data)
    if form.user is None:
        raise ValidationError('Specified user does not exist')


class Form(BaseForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('csrf_enabled', not current_app.testing)
        super(Form, self).__init__(*args, **kwargs)


class EmailFormMixin():
    email = TextField("Email Address",
        validators=[email_required,
                    email_validator])


class UserEmailFormMixin():
    user = None
    email = TextField("Email Address",
        validators=[email_required,
                    email_validator,
                    valid_user_email])


class UniqueEmailFormMixin():
    email = TextField("Email Address",
        validators=[email_required,
                    email_validator,
                    unique_user_email])


class PasswordFormMixin():
    password = PasswordField("Password",
        validators=[password_required])


class NewPasswordFormMixin():
    password = PasswordField("Password",
        validators=[password_required,
                    Length(min=6, max=128)])

class PasswordConfirmFormMixin():
    password_confirm = PasswordField("Retype Password",
        validators=[EqualTo('password', message="Passwords do not match")])


class NextFormMixin():
    next = HiddenField()


class RegisterFormMixin():
    submit = SubmitField("Register")


class SendConfirmationForm(Form, UserEmailFormMixin):
    """The default forgot password form"""

    submit = SubmitField("Resend Confirmation Instructions")

    def __init__(self, *args, **kwargs):
        super(SendConfirmationForm, self).__init__(*args, **kwargs)
        if request.method == 'GET':
            self.email.data = request.args.get('email', None)

    def validate(self):
        if not super(SendConfirmationForm, self).validate():
            return False
        if self.user.confirmed_at is not None:
            self.email.errors.append(get_message('ALREADY_CONFIRMED')[0])
            return False
        return True


class ForgotPasswordForm(Form, UserEmailFormMixin):
    """The default forgot password form"""

    submit = SubmitField("Recover Password")


class PasswordlessLoginForm(Form, UserEmailFormMixin):
    """The passwordless login form"""

    submit = SubmitField("Send Login Link")

    def __init__(self, *args, **kwargs):
        super(PasswordlessLoginForm, self).__init__(*args, **kwargs)

    def validate(self):
        if not super(PasswordlessLoginForm, self).validate():
            return False
        if not self.user.is_active():
            self.email.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False
        return True


class LoginForm(Form, NextFormMixin):
    """The default login form"""
    email = TextField('Email Address')
    password = PasswordField('Password')
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

    def validate(self):
        super(LoginForm, self).validate()

        if self.email.data.strip() == '':
            self.email.errors.append('Email not provided')
            return False

        if self.password.data.strip() == '':
            self.password.errors.append('Password not provided')
            return False

        self.user = _datastore.find_user(email=self.email.data)

        if self.user is None:
            self.email.errors.append('Specified user does not exist')
            return False
        if not verify_password(self.password.data, self.user.password):
            self.password.errors.append('Invalid password')
            return False
        if requires_confirmation(self.user):
            self.email.errors.append(get_message('CONFIRMATION_REQUIRED')[0])
            return False
        if not self.user.is_active():
            self.email.errors.append(get_message('DISABLED_ACCOUNT')[0])
            return False
        return True

class NewFormFields():
    name = TextField('Name', [validators.Length(min=1, max=25)])
    street = TextField('street', [validators.Length(min=1, max=25)])
    number = TextField('number', [validators.Length(min=1, max=25)])
    bus = TextField('bus', [validators.Length(min=1, max=25)])
    postalcode = TextField('postalcode', [validators.Length(min=1, max=25)])
    gemeente = TextField('gemeente', [validators.Length(min=1, max=25)])
    geboortedatum = TextField('geboortedatum', [validators.Length(min=1, max=25)])
    telephone = TextField('telephone', [validators.Length(min=1, max=25)])
    actief_lid = BooleanField('actief_lid')
    membership_dues = TextField('membership_dues', [validators.Length(min=1, max=25)])
    member_since = TextField('member_since', [validators.Length(min=1, max=25)])
    show_telephone = BooleanField('show_telephone')
    show_email = BooleanField('show_email')   

class ConfirmRegisterForm(Form, RegisterFormMixin, UniqueEmailFormMixin, NewPasswordFormMixin, NewFormFields):
    def to_dict(self):
        return dict(
           	email=self.email.data,
            password=self.password.data,
           	name=self.name.data,
           	street=self.street.data,
       	    number=self.number.data,
           	bus=self.bus.data,
           	postalcode=self.postalcode.data,
       	    gemeente=self.gemeente.data,
           	geboortedatum=self.geboortedatum.data,
           	telephone=self.telephone.data,
       	    actief_lid=self.actief_lid.data,
           	membership_dues=self.membership_dues.data,
           	member_since=self.member_since.data,
           	show_telephone=self.show_telephone.data,
           	show_email=self.show_email.data)

class RegisterForm(ConfirmRegisterForm, PasswordConfirmFormMixin):
    pass


class ResetPasswordForm(Form, NewPasswordFormMixin, PasswordConfirmFormMixin):
    """The default reset password form"""

    submit = SubmitField("Reset Password")
