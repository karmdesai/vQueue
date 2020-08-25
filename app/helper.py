from plivo import plivoxml

def getAvailableNumbers(plivoClient, chosenCountry):
    allNums = []
    localNums = plivoClient.numbers.search(country_iso=chosenCountry, type='local')

    for record in localNums["objects"]:
        allNums.append(record["number"])

    return allNums

def createNumber(plivoClient, phoneNumber):
    response = plivoClient.numbers.buy(number=phoneNumber)

def sendMessage(plivoClient, fromNumber, toNumber, messageToSend):
    sentMessage = plivoClient.messages.create(src=fromNumber, dst=toNumber, text=messageToSend)

def respondWith(responseItem, fromNumber, toNumber, messageToSend):
    responseItem.add(
        plivoxml.MessageElement(
            messageToSend,
            src=toNumber,
            dst=fromNumber))

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