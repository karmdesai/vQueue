import requests
from app import app
from flask import render_template, request, url_for, redirect, session
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from random import randint

# add a secret key to use sessions
app.config['SECRET_KEY'] = 'changeLater'

# get user input for starting variables
@app.route('/start')
def start():
    return render_template('start.html', title='Get Started')

# initialize a session using given variables
@app.route('/boot', methods=['POST'])
def boot():
    # if form has been filled out...
    if request.method == 'POST':
        # store the variables...
        session['businessName'] = request.form['getName']
        session['phoneNumber'] = request.form['getNumber']
        session['maxCapacity'] = int(request.form['maxCapacity'])
        session['currentCustomers'] = int(request.form['currentCustomers'])
        session['currentQueue'] = []

        # and redirect the user to dashboard.
        return redirect(url_for('dashboard'))

    # otherwise...
    else:
        # redirect the user to the start page
        return redirect(url_for('start'))

# session dashboard page
@app.route('/')
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # if the user has initialized variables...
    if session.get('maxCapacity') != None:
        # return the dashboard page with updated content
        return render_template('dashboard.html', name=session.get('businessName'), 
            number=session.get('phoneNumber'), maxCapacity=session.get('maxCapacity'), 
            curCustomers=session.get('currentCustomers'), curQueue=session.get('currentQueue'))

    # otherwise...
    else:
        # redirect the user to the start page
        return redirect(url_for('start'))

@app.route('/subtract', methods=['POST'])
def subtract():
    # assume a customer has left the store
    session['currentCustomers'] -= 1

    return redirect(url_for('dashboard'))

@app.route('/remove', methods=['POST'])
def remove():
    # look through the queue...
    for position, eachQueuer in enumerate(session.get('currentQueue')):
        # find the requested user's position...
        if eachQueuer['groupName'] == request.form['removeButton']:
            # and remove them.
            session['currentQueue'].pop(position)
            session.modified = True

    return redirect(url_for('dashboard'))
            
@app.route('/add', methods=['POST'])
def add():
    # get the customers information...
    manualCustomer = {
        'groupName': request.form['addCustomer'],
        'numPeople': request.form['numPeople']
    }

    # and manually add the customer to the queue.
    session['currentQueue'].append(manualCustomer)
    session.modified = True

    return redirect(url_for('dashboard'))

@app.route('/text', methods=['POST'])
def text():
    # get the incoming message
    sentFrom = request.values.get('From', None)
    incomingMessage = request.values.get('Body', None).upper()

    # handling the message
    response = MessagingResponse()
    message = response.message()
    haveResponded = False