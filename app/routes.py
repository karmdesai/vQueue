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
from flask import render_template, redirect, url_for, session, request, flash, jsonify

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
        rCustomers=cBusiness['rCustomers'])


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
    sentFrom = request.values.get('From', None)
    sentTo = request.values.get('To', None)
    incomingMessage = request.values.get('Body', None).upper()

    # handling the message
    response = MessagingResponse()
    message = response.message()
    haveResponded = False

    users = mongo.db.users
    cBusiness = users.find_one({'uPhone': sentTo})

    if cBusiness['rMax'] == 0:
        currentlyActive = False
    else:
        currentlyActive = True

    if 'JOIN' in incomingMessage:
        if currentlyActive:
            message.body("Before I add you to the queue, please respond with the number of people in your group.")
            message.body("If you are here by yourself, just respond with 1.")

            session['triedJoining'] = True

        else:
            message.body("We are currently not using the VQS. JSON: {}".format(cBusiness))

    else:
        if 'triedJoining' in session:
            if isInt(incomingMessage):
                if int(incomingMessage) <= 6:
                    if sentFrom not in findAllValues(cBusiness['rQueue'], 'cID'):

                        if (cBusiness['rMax'] - cBusiness['rCustomers']) >= int(incomingMessage):
                            message.body('There is enough space inside the store. Just come inside.')

                            changeRCustomers(document=users, ID=cBusiness['_id'],
                                rCustomers=cBusiness['rCustomers'] + int(incomingMessage))


                        else:
                            addToQ(document=users, ID=cBusiness['_id'], 
                                cID=sentFrom, groupSize=int(incomingMessage))

                            newCustomer = {
                                'cID': sentFrom,
                                'groupSize': int(incomingMessage)
                            }

                            message.body('I added you to the queue!')

                    else:
                        message.body('You are already in the queue. You cannot join again!')

                    session['triedJoining'] = False

                else:
                    message.body('Only 6 people can join the queue with one number.')
                    message.body('Please try again with a smaller number of people')
            else:
                message.body('Please enter only a number.')
        else:
            message.body('I cannot help with that.')

    return str(response)

@app.route('/update', methods=['GET', 'POST'])
def update():
    users = mongo.db.users
    bName = request.form.get('bName')
    cBusiness = users.find_one({'bName': bName})

    return jsonify(rQueue=cBusiness['rQueue'], rCustomers=cBusiness['rCustomers'])