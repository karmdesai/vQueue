from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField, EmailField
from wtforms.validators import DataRequired, NumberRange, Length
from app import client
from app.helper import getAvailableNumbers

class LoginForm(FlaskForm):
    uName = EmailField('Your Email', validators=[DataRequired()])
    uPassword = PasswordField('Your Password', validators=[DataRequired()])
    
    submitNow = SubmitField('Login')

class RegisterForm(FlaskForm):
    uName = EmailField("Your Email", validators=[DataRequired(), Length(min=3, max=24)])
    uPassword = PasswordField('Your Password', validators=[DataRequired(), Length(min=8, max=20)])
    bName = StringField("Your Business's Name", validators=[DataRequired(), Length(min=3, max=24)])

    uPhone = SelectField('Choose a Phone Number', choices=getAvailableNumbers(client, "CA"), validators=[DataRequired()])

    submitNow = SubmitField('Sign Up')

class CreateRoomForm(FlaskForm):
    rMax = IntegerField("Your Store's Max Capacity", validators=[DataRequired(), NumberRange(min=1)])
    rCustomers = IntegerField('# of Customers Already Inside', validators=[DataRequired()])

    submitNow = SubmitField('Create Queue')

class ManualAddForm(FlaskForm):
    cID = StringField("Person's Name", validators=[DataRequired()])
    groupSize = IntegerField("# of People", validators=[DataRequired(), NumberRange(1, 50)])

    manualAdd = SubmitField('Add User')