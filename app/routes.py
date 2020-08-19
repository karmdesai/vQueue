from flask import render_template, redirect, url_for, session
from app import app
from app import mongo
from app.forms import LoginForm, RegisterForm
import bcrypt
import dns

@app.route('/')
@app.route('/index')
def index():
    if 'username' in session:
        user = {'username': session['username']}
    else:
        user = {'username': 'Not Logged In'}
    return render_template('index.html', title='Home', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    users = mongo.db.users

    if form.validate_on_submit():
        loginUser = users.find_one({'username': form.username.data})

        if loginUser:
            if bcrypt.hashpw((form.password.data).encode('utf-8'), loginUser['password']) == loginUser['password']:
                session['username'] = form.username.data

                return redirect(url_for('index'))

        return 'Invalid Password/Email Combination'

    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    users = mongo.db.users

    if form.validate_on_submit():
        existingUser = users.find_one({'username' : form.username.data})

        if existingUser is None:
            hashedPass = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt())

            users.insert(
                {
                    'username': form.username.data, 
                    'password' : hashedPass, 
                    'queue': []
                }
            )
            session['username'] = form.username.data

            return redirect(url_for('index'))
        
        return 'That Username Already Exists!'

    return render_template('register.html', title='Register', form=form)