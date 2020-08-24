def changeAllR(document, ID, rMax, rCustomers, rQueue):
    document.update({
            '_id': ID
        }, 
        {
            '$set': {
                'rMax': rMax,
                'rCustomers': rCustomers,
                'rQueue': rQueue
            }
        }, upsert=False)

def changeRCustomers(document, ID, rCustomers):
    document.update({
            '_id': ID
        }, 
        {
            '$set': {
                'rCustomers': rCustomers
            }
        }, upsert=False)

def addToQ(document, ID, cID, groupSize):
    document.update({
            '_id': ID
        }, 
        {
            '$push': {
                'rQueue': {
                    'cID': cID,
                    'groupSize': groupSize
                }
            }
        }, upsert=False)

def removeFromQ(document, ID, cID):
    document.update({
            '_id': ID
        }, 
        {
            '$pull': {
                'rQueue': {
                    'cID': cID,
                }
            }
        }, upsert=False)

def setPassword(document, ID, newHashedPass):
    document.update({
            '_id': ID
        }, 
        {
            '$set': {
                'uPassword': newHashedPass
            }
        }, upsert=False)