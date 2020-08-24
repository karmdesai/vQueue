from flask import Flask
from config import Config
from twilio.rest import Client
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)

client = Client(app.config['TWILIO_ACCOUNT_SID'], 
    app.config['TWILIO_AUTH_TOKEN'])
mongo = PyMongo(app)
bootstrap = Bootstrap(app)

from app import routes