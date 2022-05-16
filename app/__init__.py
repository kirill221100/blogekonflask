from flask import Flask
from flask_mail import Mail
from app.config import Config
from app.models import db
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
mail = Mail(app)
db.init_app(app)
migrate = Migrate(app, db)



@app.before_first_request
def create_tables():
    db.create_all()

from app.views import *