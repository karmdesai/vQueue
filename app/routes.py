from flask import render_template, redirect, url_for, session
from app import app
from app import mongo
from app.forms import LoginForm, RegisterForm, CreateRoomForm
import bcrypt
import dns

@app.route('/')
@app.route('/index')
def index():
    if 'uName' in session:
        user = {'uName': session['username']}
    else:
        user = {'uName': 'Not Logged In'}

    return render_template('index.html', title='Home', user=user)

@app.route('/create', methods=['GET', 'POST'])
def create():
    form = CreateRoomForm()
    users = mongo.db.users
    
    if 'uName' in session:
        currentUser = users.find_one({'uName': session['uName']})

        if form.validate_on_submit():
            currentUser['rMax'] = form.rMax.data
            currentUser['rCustomers'] = form.rCustomers.data
            currentUser['rQueue'] = [{
                "phoneNo": +14165401552
            }]

            session['activeRoom'] = True

            return redirect(url_for('queue'))

    else:
        return redirect(url_for('login'))

    return render_template('create.html', title='Create', form=form)

@app.route('/queue', methods=['GET', 'POST'])
def queue():
    users = mongo.db.users

    if 'uName' in session:
        if 'activeRoom' in session:
            if session['activeRoom'] == True:
                currentUser = users.find_one({'uName': session['uName']})

            else:
                return redirect(url_for('create'))
        else:
            return redirect(url_for('create'))
    else:
        return redirect(url_for('login'))

    return render_template('queue.html', title='Queue', rCustomers=currentUser['rCustomers'], rQueue=currentUser['rQueue'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    users = mongo.db.users

    if form.validate_on_submit():
        loginUser = users.find_one({'uName': form.uName.data})

        if loginUser:
            if bcrypt.hashpw((form.uPassword.data).encode('utf-8'), loginUser['uPassword']) == loginUser['uPassword']:
                session['uName'] = form.uName.data

                return redirect(url_for('create'))

        return 'Invalid Password/Email Combination'

    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    users = mongo.db.users

    if form.validate_on_submit():
        existingUser = users.find_one({'uName': form.uName.data})

        if existingUser is None:
            hashedPass = bcrypt.hashpw(form.uPassword.data.encode('utf-8'), bcrypt.gensalt())

            users.insert(
                {
                    'uName': form.uName.data, 
                    'uPassword': hashedPass, 
                    'rMax': 0,
                    'rCustomers': 0,
                    'rQueue': []
                }
            )

            session['uName'] = form.uName.data

            return redirect(url_for('create'))
        
        return 'That Username Already Exists!'

    return render_template('register.html', title='Register', form=form)