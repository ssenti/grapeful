from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_babel import _, lazy_gettext as _l
from app.models import User


class LoginForm(FlaskForm):
    username = StringField(_l('username'), validators=[
        DataRequired()])
    password = PasswordField(_l('password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('remember me'))
    submit = SubmitField(_l('login'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('username'), validators=[DataRequired()])
    email = StringField(_l('email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('repeat password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('please use a different username'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('please use a different email address'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('request password reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('repeat password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('request password reset'))
