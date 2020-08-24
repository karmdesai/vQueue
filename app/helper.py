def getAvailableNumbers(twilioClient, chosenCountry):
    allNums = []
    localNums = twilioClient.available_phone_numbers(chosenCountry).local.list(limit=50)

    for record in localNums:
        allNums.append(record.phone_number)

    return allNums

def sendMessage(twilioClient, fromNumber, toNumber, messageToSend):
    sentMessage = twilioClient.messages.create(body=messageToSend, from_=fromNumber,to=toNumber)

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

def findAllValues(dictsInList, keyName):
    finalValues = []

    for eachDict in dictsInList:
        finalValues.append(eachDict[keyName])

    return finalValues