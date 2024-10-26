from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class ConfigForm(FlaskForm):
    email = StringField('FOFA Email', validators=[DataRequired()])
    key = StringField('FOFA Key', validators=[DataRequired()])
    submit = SubmitField('保存配置')
