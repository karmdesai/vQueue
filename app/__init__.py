from flask import Flask
from config import Config
from plivo import RestClient
from flask_pymongo import PyMongo
from flask_bootstrap import Bootstrap
from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)

client = RestClient(app.config['PLIVO_AUTH_ID'], 
    app.config['PLIVO_AUTH_TOKEN'])
mongo = PyMongo(app)
bootstrap = Bootstrap(app)

from app import routes