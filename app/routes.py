import dns
import jwt
import bcrypt
import requests
from time import time

from app import app
from app import mongo
from app import client

from app.relations import changeAllR, changeRCustomers, addToQ, removeFromQ, setPassword
from app.forms import LoginForm, RegisterForm, CreateRoomForm, ManualAddForm, ResetPasswordRequestForm, ResetPasswordForm
from app.helper import sendMessage, isInt, isPhoneNumber, findAllValues, createNumber
from app.email import sendEmail

from twilio.twiml.messaging_response import MessagingResponse
from flask import render_template, redirect, url_for
from flask import session, request, flash, jsonify

@app.route('/index', methods=['POST', 'GET'])
def index():
    form = CreateRoomForm()
    users = mongo.db.users

    if 'uName' in session:
        cBusiness = users.find_one({'uName': session['uName']})

        if form.validate_on_submit():
            if form.rCustomers.data <= form.rMax.data:
                changeAllR(document=users, ID=cBusiness['_id'], rMax=form.rMax.data, 
                    rCustomers=form.rCustomers.data, rQueue=[])

                session['activeRoom'] = True

                return redirect(url_for('queue'))
            else:
                flash("""The number of customers already inside your building 
                    must be less than the maximum capacity. Please try again.""")

                return redirect(url_for('index'))

    else:
        return redirect(url_for('login'))

    return render_template('index.html', title='Home', form=form, bName=cBusiness['bName'])

@app.route('/subtract')
def subtract():
    users = mongo.db.users

    if 'activeRoom' in session:
        cBusiness = users.find_one({'uName': session['uName']})

        if cBusiness['rCustomers'] > 0:
            changeRCustomers(document=users, ID=cBusiness['_id'],
                rCustomers=cBusiness['rCustomers'] - 1)

        if len(cBusiness['rQueue']) > 0:
            nextCustomer = cBusiness['rQueue'][0]

            if (cBusiness['rMax'] - cBusiness['rCustomers'] + 1) >= nextCustomer['groupSize']:
                changeRCustomers(document=users, ID=cBusiness['_id'],
                    rCustomers=cBusiness['rCustomers'] + nextCustomer['groupSize'])

                removeFromQ(document=users, ID=cBusiness['_id'],
                    cID=nextCustomer['cID'])
                    
                if isPhoneNumber(nextCustomer['cID']):
                    sendMessage(client, cBusiness['uPhone'], 
                    nextCustomer['cID'], 'You can come inside now! Please do.')
                                    
                else:
                    flash("""There is enough space to call {} into the store.
                    I have removed them from the queue. Please remember to call them 
                    inside.""".format(nextCustomer['cID'], nextCustomer['groupSize']))

                if len(cBusiness['rQueue']) > 0:
                    furtherCustomer = cBusiness['rQueue'][0]

                    if isPhoneNumber(furtherCustomer['cID']):
                        sendMessage(client, cBusiness['uPhone'], furtherCustomer['cID'], 
                                'You are now first in line. You will be called into the store shortly.')
                             
        return redirect(url_for('queue'))

    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    users = mongo.db.users

    if 'uName' in session:
        cBusiness = users.find_one({'uName': session['uName']})

        changeAllR(document=users, ID=cBusiness['_id'], rMax=0, rCustomers=0, rQueue=[])

        session.pop('uName')

    return redirect(url_for('login'))

@app.route('/remove/<cID>')
def remove(cID):
    users = mongo.db.users

    if 'activeRoom' in session:
        cBusiness = users.find_one({'uName': session['uName']})

        removeFromQ(document=users, ID=cBusiness['_id'],
                    cID=cID)

        if len(cBusiness['rQueue']) > 0:
            furtherCustomer = cBusiness['rQueue'][0]

            if isPhoneNumber(furtherCustomer['cID']):
                sendMessage(client, cBusiness['uPhone'], furtherCustomer['cID'], 
                        'You are now first in line. You will be called into the store shortly.')

        return redirect(url_for('queue'))

    else:
        return redirect(url_for('index'))

@app.route('/queue', methods=['GET', 'POST'])
def queue():
    users = mongo.db.users
    form = ManualAddForm()

    if 'activeRoom' in session:
        cBusiness = users.find_one({'uName': session['uName']})

        if form.validate_on_submit():
            if (cBusiness['rMax'] - cBusiness['rCustomers']) >= form.groupSize.data and len(cBusiness['rQueue']) == 0:
                flash("""There is enough space for '{}' to be inside. Please call them.""".format(form.cID.data))

                changeRCustomers(document=users, ID=cBusiness['_id'],
                    rCustomers=cBusiness['rCustomers'] + form.groupSize.data)

            else:
                if form.cID.data not in findAllValues(cBusiness['rQueue'], 'cID'):
                    addToQ(document=users, ID=cBusiness['_id'], 
                        cID=form.cID.data, groupSize=form.groupSize.data)    

                else:
                    flash("""The name '{}' is already taken. Please choose a different 
                    name.""".format(form.cID.data))

            return redirect(url_for('queue'))

    else:
        flash("You have not created a queue yet.")

        return redirect(url_for('index'))

    return render_template('queue.html', title='Queue', bName=cBusiness['bName'], form=form, 
        rMax=cBusiness['rMax'], rCustomers=cBusiness['rCustomers'], 
        rQueue=cBusiness['rQueue'], uPhone=cBusiness['uPhone'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    users = mongo.db.users

    if 'uName' not in session:
        if 'activeRoom' not in session:
            if form.validate_on_submit():
                loginUser = users.find_one({'uName': form.uName.data})

                if loginUser:
                    if bcrypt.hashpw((form.uPassword.data).encode('utf-8'), loginUser['uPassword']) == loginUser['uPassword']:
                        session['uName'] = form.uName.data

                        return redirect(url_for('index'))

                flash("Invalid Email/Password combination. Try again.")

                return redirect(url_for('login'))

    else:
        return redirect(url_for('index'))

    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    users = mongo.db.users

    if 'activeRoom' not in session:
        if form.validate_on_submit():
            existingUser = users.find_one({'uName': form.uName.data})

            if existingUser is None:
                hashedPass = bcrypt.hashpw(form.uPassword.data.encode('utf-8'), bcrypt.gensalt())

                createNumber(client, form.uPhone.data)

                users.insert(
                    {
                        'uName': form.uName.data, 
                        'uPassword': hashedPass, 
                        'bName': form.bName.data,
                        'uPhone': form.uPhone.data,
                        'rMax': 0,
                        'rCustomers': 0,
                        'rQueue': []
                    }
                )

                session['uName'] = form.uName.data

                return redirect(url_for('index'))
            
            flash("That username already exists. Use another username or login instead.")
            return redirect(url_for('register'))
    else:
        return redirect(url_for('index'))

    return render_template('register.html', title='Register', form=form)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    # get the incoming message
    sentTo = request.values.get('To', None)
    sentFrom = request.values.get('From', None)
    incomingMessage = request.values.get('Body', None).upper()

    # handling the message
    response = MessagingResponse()
    message = response.message()
    haveResponded = False

    users = mongo.db.users
    cBusiness = users.find_one({'uPhone': sentTo})

    if cBusiness['rMax'] == 0:
        message.body("Welcome to {}!".format(cBusiness['bName']))
        message.body("We are currently not using a virtual queue.")
        message.body("Please visit the store for more information.")

        return str(response)

    if 'JOIN' in incomingMessage:
        message.body("Welcome to {}!".format(cBusiness['bName']))
        message.body("Before you join the queue, please respond")
        message.body('with the number of people in your group.')
        message.body("If you're here by yourself, just respond with 1.")

        session['triedJoining'] = True

        haveResponded = True

    if isInt(incomingMessage) and ('triedJoining' in session):

        if sentFrom not in findAllValues(cBusiness['rQueue'], 'cID'):
            availableSpace = cBusiness['rMax'] - cBusiness['rCustomers']

            if int(incomingMessage) <= 8:

                if availableSpace >= int(incomingMessage) and len(cBusiness['rQueue']) == 0:
                    message.body('There is enough space inside the building.')
                    message.body('Your group can enter the store right away!')

                    changeRCustomers(document=users, ID=cBusiness['_id'],
                        rCustomers=cBusiness['rCustomers'] + int(incomingMessage))

                else:
                    message.body("Good news! I've added you to the queue.")
                    message.body("If you want to check your position in line, type 'CHECK'.")
                    message.body("I will let you know when you can enter the building.")

                    addToQ(document=users, ID=cBusiness['_id'], 
                        cID=sentFrom, groupSize=int(incomingMessage))

            else:
                message.body('Only up to 8 people can join the queue using one phone number.')
                message.body('If your group has more than 8 people, please visit the building.')

        else:
            message.body('You are already in the queue!')

            userPosition = findAllValues(cBusiness['rQueue'], 'cID').index(sentFrom)
            message.body("You are currently #{} in line.".format(userPosition + 1))

        haveResponded = True

    if 'CHECK' in incomingMessage:
        if sentFrom in findAllValues(cBusiness['rQueue'], 'cID'):
            userPosition = findAllValues(cBusiness['rQueue'], 'cID').index(sentFrom)
            message.body("You are currently #{} in line.".format(userPosition + 1))

        else:
            message.body('You are not in the queue as of now.')
            message.body("Type 'JOIN' to get started!")

        haveResponded = True

    if not haveResponded:
        message.body("Sorry, I don't know how to help with that.")
        message.body("If you want to join the queue, type 'JOIN'.")
        message.body("If you want to check your position in line, type 'CHECK'.")

    return str(response)

@app.route('/update', methods=['GET', 'POST'])
def update():
    users = mongo.db.users
    bName = request.form.get('bName')
    cBusiness = users.find_one({'bName': bName})

    return jsonify(rQueue=cBusiness['rQueue'], rCustomers=cBusiness['rCustomers'])

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    form = ResetPasswordRequestForm()
    users = mongo.db.users

    if 'uName' in session:
        return redirect(url_for('index'))

    if form.validate_on_submit():
        existingUser = users.find_one({'uName': form.uEmail.data})

        if existingUser:
            sendPasswordReset(existingUser['uName'])
            
            flash('Check your email address for instructions on how to reset your password!')
            return redirect(url_for('login'))

        else:
            flash('You have not created an account yet. Please register with us!')
            return redirect(url_for('register'))

    return render_template('reset.html', title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    users = mongo.db.users

    if 'uName' in session:
        return redirect(url_for('index'))

    user = verifyToken(token)

    if not user:
        return redirect(url_for('index'))

    form = ResetPasswordForm()
    cBusiness = users.find_one({'uName': user})

    if form.validate_on_submit():
        hashedPass = bcrypt.hashpw(form.uPass.data.encode('utf-8'), bcrypt.gensalt())

        setPassword(users, ID=cBusiness['_id'], newHashedPass=hashedPass)
        flash('Success! Your password has been reset.')
        
        return redirect(url_for('login'))

    return render_template('reset_password.html', form=form)

def getResetToken(uEmail, expiresIn=1000):
    return jwt.encode(
        {'resetPassword': uEmail, 'expTime': time() + expiresIn},
            'SECRETS', algorithm='HS256').decode('utf-8')

def verifyToken(token):
    users = mongo.db.users

    try:
        uEmail = jwt.decode(token, 'SECRETS',
                    algorithms=['HS256'])['resetPassword']
    except:
        return

    return users.find_one({'uName': uEmail})['uName']

def sendPasswordReset(user):
    token = getResetToken(user)

    sendEmail('[vQueue] Reset Your Password',
               sender=app.config['MAIL_USERNAME'],
               recipients=user,
               text_body=render_template('email/reset.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset.html',
                                         user=user, token=token))