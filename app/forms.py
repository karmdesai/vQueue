from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange

class LoginForm(FlaskForm):
    uName = StringField('Username', validators=[DataRequired()])
    uPassword = PasswordField('Password', validators=[DataRequired()])
    
    submitNow = SubmitField('Login')

class RegisterForm(FlaskForm):
    uName = StringField('Username', validators=[DataRequired()])
    uPassword = PasswordField('Password', validators=[DataRequired()])
    bName = StringField("Your Business's Name (Customers Will See This)", validators=[DataRequired()])
    uPhone = StringField('Your Phone Number', validators=[DataRequired()])

    submitNow = SubmitField('Sign Up')

class CreateRoomForm(FlaskForm):
    rMax = IntegerField('Max Capacity', validators=[DataRequired(), NumberRange(min=1)])
    rCustomers = IntegerField('Current Customers', validators=[DataRequired(), NumberRange(1, 50)])

    createRoom = SubmitField('Create Room')

class endSessionForm(FlaskForm):
    endSession = SubmitField('End Session')

class subtractRemoveForm(FlaskForm):
    subtractCustomer = SubmitField('-')

class manualAddForm(FlaskForm):
    cID = StringField("Person's Name", validators=[DataRequired()])
    groupSize = IntegerField("# of People", validators=[DataRequired(), NumberRange(1, 50)])

    submitName = SubmitField('Add User')

class manualRemoveForm(FlaskForm):
    userID = SelectField('Choose A User To Remove', choices=[], validators=[DataRequired()])
    removeUser = SubmitField('Remove User')