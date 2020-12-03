from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, NumberRange, Length, Email
from app import client
from app.helper import getAvailableNumbers

standardInput = {'class': 'input is-size-5'}
smallInput = {'class': 'input is-size-6'}
submitInput = {'class': 'button is-primary is-size-5'}

class LoginForm(FlaskForm):
    uName = EmailField('Your Email', validators=[DataRequired(), Email()], render_kw=standardInput)
    uPassword = PasswordField('Your Password', validators=[DataRequired()], render_kw=standardInput)
    
    submitNow = SubmitField('Login', render_kw=submitInput)

class RegisterForm(FlaskForm):
    uName = EmailField("Your Email", validators=[DataRequired(), Email()], render_kw=smallInput)
    uPassword = PasswordField('Your Password', validators=[DataRequired(), Length(min=8, max=24)], render_kw=smallInput)
    bName = StringField("Your Business's Name", validators=[DataRequired(), Length(min=3, max=24)], render_kw=smallInput)

    uPhone = SelectField('Choose a Phone Number', choices=getAvailableNumbers(client, "CA"), validators=[DataRequired()])

    submitNow = SubmitField('Sign Up', render_kw=submitInput)

class CreateRoomForm(FlaskForm):
    rMax = IntegerField("Your Store's Max Capacity", validators=[DataRequired(), NumberRange(min=1)], render_kw=standardInput)
    rCustomers = IntegerField('# of Customers Already Inside', validators=[DataRequired(), NumberRange(min=0)], render_kw=standardInput)

    submitNow = SubmitField('Create Queue', render_kw=submitInput)

class ManualAddForm(FlaskForm):
    cID = StringField("Person's Name", validators=[DataRequired()], render_kw=standardInput)
    groupSize = IntegerField("# of People", validators=[DataRequired(), NumberRange(1, 50)], render_kw=standardInput)

    manualAdd = SubmitField('Add User', render_kw=submitInput)

class ResetPasswordRequestForm(FlaskForm):
    uEmail = EmailField('Your Email', validators=[DataRequired(), Email()], render_kw=standardInput)
    submitNow = SubmitField('Request Password Reset', render_kw=submitInput)

class ResetPasswordForm(FlaskForm):
    uPass = PasswordField('Your New Password', validators=[DataRequired(), Length(min=8, max=24)], render_kw=standardInput)
    submitNow = SubmitField('Reset Password', render_kw=submitInput)