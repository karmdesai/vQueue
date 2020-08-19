from flask import Flask
from config import Config
from flask_pymongo import PyMongo
from twilio.rest import Client

app = Flask(__name__)
app.config.from_object(Config)
mongo = PyMongo(app)

account_sid = 'ACe6de0e4556a89b8f10f9632c66035b2b'
auth_token = 'c8cc4c6159588b410554d5361f6be43c'
client = Client(account_sid, auth_token)

from app import routes