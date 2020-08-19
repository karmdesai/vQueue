from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import DataRequired, NumberRange

class LoginForm(FlaskForm):
    uName = StringField('Username', validators=[DataRequired()])
    uPassword = PasswordField('Password', validators=[DataRequired()])
    
    submitNow = SubmitField('Login')

class RegisterForm(FlaskForm):
    uName = StringField('Username', validators=[DataRequired()])
    uPassword = PasswordField('Password', validators=[DataRequired()])
    uPhone = StringField('Your Phone Number', validators=[DataRequired()])

    submitNow = SubmitField('Sign Up')

class CreateRoomForm(FlaskForm):
    rMax = IntegerField('Max Capacity', validators=[DataRequired(), NumberRange(min=1)])
    rCustomers = IntegerField('Current Customers', validators=[DataRequired(), NumberRange(1, 50)])

    createRoom = SubmitField('Create Room')