from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FileField
from wtforms.validators import ValidationError, DataRequired, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User
from flask_wtf.file import FileAllowed


class EditProfileForm(FlaskForm):
    username = StringField(_l('username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('about me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('please use a different username.'))


class EmptyForm(FlaskForm):
    submit = SubmitField('submit')


class PostForm(FlaskForm):
    title = TextAreaField(_l(''), validators=[DataRequired(),
    Length(min=1, max=25, message=(u'title can only be up to 25 characters'))])
    post = TextAreaField(_l(''), validators=[DataRequired(),
    Length(min=1, max=500, message=(u'the description can only be up to 500 characters'))])
    filename = FileField('')
    submit = SubmitField(_l('grape it \U0001F347'))
