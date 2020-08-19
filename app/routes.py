from flask import render_template, redirect, url_for, session, request
from app import app
from app import mongo, client
from app.forms import LoginForm, RegisterForm, CreateRoomForm, manualAddForm, subtractRemoveForm
from twilio.twiml.messaging_response import MessagingResponse
import bcrypt
import dns

def sendMessage(fromNumber, toNumber, message):
    message = client.messages.create(body=message, from_=fromNumber,to=toNumber)

@app.route('/')
@app.route('/index')
def index():
    if 'uName' in session:
        user = {'uName': session['uName']}
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
            users.update(
                {
                    '_id': currentUser['_id']
                },
                {
                    '$set': {
                        'rMax': form.rMax.data,
                        'rCustomers': form.rCustomers.data,
                        'rQueue': []
                    }
                }, upsert=False
            )

            session['activeRoom'] = True

            return redirect(url_for('queue'))

    else:
        return redirect(url_for('login'))

    return render_template('create.html', title='Create', form=form)

@app.route('/queue', methods=['GET', 'POST'])
def queue():
    users = mongo.db.users
    manualForm = manualAddForm()
    subtractForm = subtractRemoveForm()

    if 'uName' in session:
        if 'activeRoom' in session:
            if session['activeRoom'] == True:
                currentUser = users.find_one({'uName': session['uName']})

                if manualForm.validate_on_submit():
                    users.update(
                        {'_id': currentUser['_id']},
                        {
                            '$push': {
                                'rQueue': {
                                    'cID': form.cID.data,
                                    'groupSize': form.groupSize.data
                                }
                            }
                        }, upsert=False
                    )

                    return redirect(url_for('queue'))

                if subtractForm.validate_on_submit():
                    users.update(
                        {'_id': currentUser['_id']},
                        {
                            '$set': {
                                'rCustomers': currentUser['rCustomers'] - 1
                            }
                        }, upsert=False
                    )

                    nextUser = currentUser['rQueue'][0]

                    if (currentUser['rMax'] - currentUser['rCustomers']) >= nextUser['groupSize']:
                        if isPhoneNumber(nextUser['cID']):
                            sendMessage(currentUser['uPhone'], nextUser['cID'], 'You can come inside now! Please do.')
                        else:
                            pass
                             
                    return redirect(url_for('queue'))

            else:
                return redirect(url_for('create'))
        else:
            return redirect(url_for('create'))
    else:
        return redirect(url_for('login'))

    return render_template('queue.html', title='Queue', rCustomers=currentUser['rCustomers'], 
    rQueue=currentUser['rQueue'], manualForm=manualForm, subtractForm=subtractForm)


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
                    'bName': form.bName.data,
                    'uPhone': form.uPhone.data,
                    'rMax': 0,
                    'rCustomers': 0,
                    'rQueue': []
                }
            )

            session['uName'] = form.uName.data

            return redirect(url_for('create'))
        
        return 'That Username Already Exists!'

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
    chosenBusiness = users.find_one({'uPhone': sentTo})

    if chosenBusiness['rMax'] == 0:
        currentlyActive = False
    else:
        currentlyActive = True

    if 'JOIN' in incomingMessage:
        if currentlyActive:
            message.body("Before I add you to the queue, please respond with the number of people in your group.")
            message.body("If you are here by yourself, just respond with 1.")

            session['triedJoining'] = True

        else:
            message.body("We are currently not using the VQS. JSON: {}".format(chosenBusiness))

    else:
        if 'triedJoining' in session:
            if isInt(incomingMessage):
                if int(incomingMessage) <= 6:
                    if (chosenBusiness['rMax'] - chosenBusiness['rCustomers']) >= int(incomingMessage):
                        message.body('There is enough space inside the store. Just come inside.')

                        users.update(
                        {'_id': chosenBusiness['_id']},
                        {
                            '$set': {
                                'rCustomers': chosenBusiness['rCustomers'] + int(incomingMessage)
                            }             
                        }, upsert=False)


                    else:
                        users.update(
                        {'_id': chosenBusiness['_id']},
                        {
                            '$push': {
                                'rQueue': {
                                    'cID': sentFrom,
                                    'groupSize': int(incomingMessage)
                                }
                            }             
                        }, upsert=False)

                        message.body('I added you to the queue!')

                    session['triedJoining'] = False

                else:
                    message.body('Only 6 people can join the queue with one number.')
                    message.body('Please try again with a smaller number of people')
            else:
                message.body('Please enter only a number.')
        else:
            message.body('I cannot help with that.')

    return str(response)

def isInt(x):
    try: 
        int(x)
        return True

    except ValueError:
        return False

def isPhoneNumber(x):
    if isInt(x[1:-1]):
        return True

    return False