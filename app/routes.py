from app import app
from flask import render_template

@app.route('/session')
def session():
    userAccount = {'name': 'Allwell Pharmacy', 'maxCapacity': 3, 'active': True}

    currentStatus = {
        'customers': 3,
        'queue': ['+16477721552', '+14169060417']
    }

    return render_template('session.html', title='Dashboard', user=userAccount, status=currentStatus)

@app.route('/done', methods=['POST'])
def done():
    userAccount = {'name': 'Allwell Pharmacy', 'maxCapacity': 3, 'active': False}

    if userAccount['active'] == False:
        return render_template('done.html', title='Done', user=userAccount)

    else:
        return render_template('error.html', title='Error', user=userAccount)