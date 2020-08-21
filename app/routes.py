import dns
import bcrypt
import requests

from app import app
from app import mongo
from app import client

from app.relations import changeAllR, changeRCustomers, addToQ, removeFromQ
from app.forms import LoginForm, RegisterForm, CreateRoomForm, ManualAddForm
from app.helper import sendMessage, isInt, isPhoneNumber, findAllValues

from twilio.twiml.messaging_response import MessagingResponse
from flask import render_template, redirect, url_for
from flask import session, request, flash, jsonify

@app.route('/')
@app.route('/index')
def index():
    if 'uName' in session:
        user = {'uName': session['uName']}
    else:
        user = {'uName': 'Not Logged In'}

    return render_template('index.html', title='Home', user=user)

@app.route('/subtract')
def subtract():
    users = mongo.db.users

    if session['activeRoom'] == True:
        cBusiness = users.find_one({'uName': session['uName']})

        if cBusiness['rCustomers'] > 0:
            changeRCustomers(document=users, ID=cBusiness['_id'],
                rCustomers=cBusiness['rCustomers'] - 1)

        if len(cBusiness['rQueue']) > 0:
            nextCustomer = cBusiness['rQueue'][0]

            if (cBusiness['rMax'] - cBusiness['rCustomers']) >= nextCustomer['groupSize']:
                if isPhoneNumber(nextCustomer['cID']):
                    sendMessage(client, cBusiness['uPhone'], 
                    nextCustomer['cID'], 'You can come inside now! Please do.')
                                    
                else:
                    flash("""There was enough space to call {} into the store. They are a group of {}.
                    I have removed them from the queue. Please remember to call them 
                    inside.""".format(nextCustomer['cID'], nextCustomer['groupSize']))

                changeRCustomers(document=users, ID=cBusiness['_id'],
                    rCustomers=cBusiness['rCustomers'] + nextCustomer['groupSize'])

                removeFromQ(document=users, ID=cBusiness['_id'],
                    cID=nextCustomer['cID'])

                             
        return redirect(url_for('queue'))

    else:
        return redirect(url_for('create'))


@app.route('/remove/<cID>')
def remove(cID):
    users = mongo.db.users

    if session['activeRoom'] == True:
        cBusiness = users.find_one({'uName': session['uName']})

        removeFromQ(document=users, ID=cBusiness['_id'],
                    cID=cID)

        return redirect(url_for('queue'))

    else:
        return redirect(url_for('create'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    form = CreateRoomForm()
    users = mongo.db.users
    
    if 'uName' in session:
        cBusiness = users.find_one({'uName': session['uName']})

        if form.validate_on_submit():
            changeAllR(document=users, ID=cBusiness['_id'], rMax=form.rMax.data, 
                rCustomers=form.rCustomers.data, rQueue=[])

            session['activeRoom'] = True

            return redirect(url_for('queue'))

    else:
        return redirect(url_for('login'))

    return render_template('create.html', title='Create', form=form)

@app.route('/queue', methods=['GET', 'POST'])
def queue():
    users = mongo.db.users
    form = ManualAddForm()

    if 'activeRoom' in session:
        if session['activeRoom'] == True:
            cBusiness = users.find_one({'uName': session['uName']})

            if form.validate_on_submit():
                if (cBusiness['rMax'] - cBusiness['rCustomers']) >= form.groupSize.data:
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
            return redirect(url_for('create'))
    else:
        return redirect(url_for('create'))

    return render_template('queue.html', title='Queue', bName=cBusiness['bName'], form=form, 
        rCustomers=cBusiness['rCustomers'], rQueue=cBusiness['rQueue'])


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

        flash("Invalid Email/Password combination. Try again.")
        return redirect(url_for('login'))

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
                    'bName': form.bName.data,
                    'uPhone': form.uPhone.data,
                    'rMax': 0,
                    'rCustomers': 0,
                    'rQueue': []
                }
            )

            session['uName'] = form.uName.data

            return redirect(url_for('create'))
        
        flash("That username already exists. Use another username or login instead.")
        return redirect(url_for('register'))

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
    
    if 'HELLO' in incomingMessage:
        message.body("Welcome to {}!".format(cBusiness['bName']))
        message.body("If you want to join the queue, type 'JOIN'.")
        message.body("If you want to check your position in line, type 'CHECK'.")
        message.body("If you want to leave the queue, type 'LEAVE'.")

    if 'JOIN' in incomingMessage:
        message.body("""Before you join the queue, please respond
                        with the number of people in your group.""")
        message.body("If you're here by yourself, just respond with 1.")

        session['triedJoining'] = True

        haveResponded = True

    if isInt(incomingMessage) and ('triedJoining' in session):

        if int(incomingMessage) <= 6:

            if sentFrom not in findAllValues(cBusiness['rQueue'], 'cID'):
                availableSpace = cBusiness['rMax'] - cBusiness['rCustomers']

                if availableSpace >= int(incomingMessage):
                    message.body('There is enough space inside the building.')
                    message.body('Your group can enter the store right away!')

                    changeRCustomers(document=users, ID=cBusiness['_id'],
                        rCustomers=cBusiness['rCustomers'] + int(incomingMessage))

                else:
                    addToQ(document=users, ID=cBusiness['_id'], 
                        cID=sentFrom, groupSize=int(incomingMessage))

                    newCustomer = {
                        'cID': sentFrom,
                        'groupSize': int(incomingMessage)
                    }

                    message.body("Good news! I've added you to the queue.")

                    userPosition = findAllValues(cBusiness['rQueue'], 'cID').index(sentFrom)
                    message.body("You are currently #{} in line.".format(userPosition + 1))

                    message.body("I will let you know when you can enter the building.")

            else:
                message.body('You are already in the queue!')

                userPosition = findAllValues(cBusiness['rQueue'], 'cID').index(sentFrom)
                message.body("You are currently #{} in line.".format(userPosition + 1))

        else:
            message.body('Only up to 6 people can join the queue using one phone number.')
            message.body('If your group has more than 6 people, please visit the building.')

        haveResponded = True

    if 'CHECK' in incomingMessage:
        userPosition = findAllValues(cBusiness['rQueue'], 'cID').index(sentFrom)
        message.body("You are currently #{} in line.".format(userPosition + 1))

        haveResponded = True

    if 'LEAVE' in incomingMessage:
        removeFromQ(document=users, ID=cBusiness['_id'], cID=sentFrom)
        message.body("You have been removed from the queue!")
        message.body("Please visit again soon.")

        haveResponded = True

    if not haveResponded:
        message.body("Sorry, I don't know how to help with that.")
        message.body("If you want to join the queue, type 'JOIN'.")
        message.body("If you want to check your position in line, type 'CHECK'.")
        message.body("If you want to leave the queue, type 'LEAVE'.")

    return str(response)

@app.route('/update', methods=['GET', 'POST'])
def update():
    users = mongo.db.users
    bName = request.form.get('bName')
    cBusiness = users.find_one({'bName': bName})

    return jsonify(rQueue=cBusiness['rQueue'], rCustomers=cBusiness['rCustomers'])