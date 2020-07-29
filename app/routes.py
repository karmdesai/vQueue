import requests
from app import app
from flask import render_template, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

global userAccount
global currentStatus

account_sid = 'ACe6de0e4556a89b8f10f9632c66035b2b'
auth_token = 'c8cc4c6159588b410554d5361f6be43c'
client = Client(account_sid, auth_token)

def sendMessage(number, message):
    message = client.messages.create(body=message, from_=userAccount['registeredNumber'],to=number)

userAccount = {'name': 'Allwell Pharmacy', 'maxCapacity': 2, 'registeredNumber': '+16474961018', 'active': False}

currentStatus = {
    'customers': 2,
    'queue': []
}

# business variables
currentQueue = currentStatus['queue']

@app.route('/')
@app.route('/session')
def session():
    global userAccount

    userAccount['active'] = True

    return render_template('session.html', title='Dashboard', user=userAccount, status=currentStatus)

@app.route('/restart', methods=['POST'])
def restart():
    return session()

@app.route('/end', methods=['POST'])
def end():
    global userAccount

    if userAccount['active'] == True:
        userAccount = {'name': 'Allwell Pharmacy', 'maxCapacity': 2, 'registeredNumber': '+16474961018', 'active': False}

        currentStatus = {
            'customers': 2,
            'queue': []
        }

    return render_template('done.html', title='Done', user=userAccount)

@app.route('/refresh', methods=['POST'])
def refresh():
    return render_template('session.html', title='Dashboard', user=userAccount, status=currentStatus)

@app.route('/left', methods=['POST'])
def left():
    global userAccount
    global currentStatus

    if userAccount['active'] == True:
        if (currentStatus['customers'] > 0):
            currentStatus['customers'] -= 1

            queueLength = len(currentStatus['queue'])

            if (queueLength > 0):
                sendMessage(currentStatus['queue'][0], 'You may now come inside the store. We are waiting for you!')
                currentStatus['queue'].pop(0)
                currentStatus['customers'] += 1

                newLength = len(currentStatus['queue'])

                if (newLength > 0):
                    sendMessage(currentStatus['queue'][0], 'You are currently #1 in line. We will let you know when it is your turn.')

    return render_template('session.html', title='Dashboard', user=userAccount, status=currentStatus)

@app.route('/text', methods=['POST'])
def text():
    global userAccount
    global currentStatus
    
    # get the incoming message
    sentFrom = request.values.get('From', None)
    incomingMessage = request.values.get('Body', None).upper()

    # handling the message
    response = MessagingResponse()
    message = response.message()
    haveResponded = False

    if userAccount['active'] == True:
        # when user texts the bot...
        if 'HELLO' in incomingMessage:
            # let them know the max amount of customers allowed...
            message.body(f'Welcome to {userAccount["name"]}, {sentFrom}. Our max capacity is {userAccount["maxCapacity"]} customers.')

            # and show them the options
            message.body(f'Type JOIN to join the queue. We will notify you when there is free space.')
            message.body(f'Type CHECK to check your position in the line.')
            message.body(f'Type LEAVE if you want to leave the queue.')

            haveResponded = True

        if 'JOIN' in incomingMessage:
            # if there is enough space in the store...
            if currentStatus["customers"] < userAccount["maxCapacity"] and len(currentStatus["queue"]) == 0:
                # let the customer in
                message.body('There is enough space to enter our store. Please come inside!')
                currentStatus["customers"] += 1

            # otherwise...
            else:
                # let them know there's not enough space
                message.body(f'Not enough space right now. Currently {currentStatus["customers"]} in the store. There are {len(currentStatus["queue"])} customers waiting.')
                    
                # if they're not in the queue...
                if sentFrom not in currentStatus["queue"]:
                    # add them to the queue
                    currentStatus["queue"].append(sentFrom)

                    message.body(f'We added you to the queue {sentFrom}! You are currently #{currentStatus["queue"].index(sentFrom) + 1} in line.')
                    message.body('We will notify you when it is your turn.')

                # if the user is in the queue, let them know what position they are at
                else:
                    message.body(f'You are already in the queue. You are currently #{currentStatus["queue"].index(sentFrom) + 1} in line.')

            haveResponded = True

        if 'CHECK' in incomingMessage:
            # if the user is in the queue, let them know what position they are at
            if sentFrom in currentStatus["queue"]:
                message.body(f'Hello, {sentFrom}. You are currently #{currentStatus["queue"].index(sentFrom) + 1} in line.')

            # otherwise...
            else:
                # tell them to join the queue
                message.body(f'You are currently not in the queue. Type JOIN to get started.')

            haveResponded = True

        if 'LEAVE' in incomingMessage:
            # if the user is in the queue...
            if sentFrom in currentStatus["queue"]:
                # remove them
                currentStatus["queue"].remove(sentFrom)
                message.body(f'Hello, {sentFrom}. You are no longer in the queue.')

            else:
                message.body(f'Hmmm... I could not find you in the queue. If you want to join the queue, type JOIN.')

            haveResponded = True

        # if no command is found...
        if haveResponded == False:
            # tell the user to try again
            message.body('Sorry, I do not know how to help with that. Type HELLO to see available options.')

    else:
        message.body('Sorry, our store is not currently using the Virtual Queuing System. Please enter the store for more details or call us.')

    return str(response)