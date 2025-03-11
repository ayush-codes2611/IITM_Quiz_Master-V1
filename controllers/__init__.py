from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from sqlalchemy.engine import Engine
from sqlalchemy import event

# Initialize app and db
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///master.db'
app.config['SECRET_KEY'] = '7564da6b69a5f4a73c57fd45'

db = SQLAlchemy(app)  # Initialize SQLAlchemy with the app
# migrate = Migrate(app, db)

# # Enable foreign key support for SQLite
# @app.before_request
# def enable_foreign_keys():
#     from sqlalchemy.engine import Engine
#     from sqlalchemy import event
#     @event.listens_for(Engine, "connect")
#     def set_sqlite_pragma(dbapi_connection, connection_record):
#         cursor = dbapi_connection.cursor()
#         cursor.execute("PRAGMA foreign_keys=ON")
#         cursor.close()

# Define the custom filter for dynamic attribute access
def get_attribute(obj, attr):
    return getattr(obj, attr, None)

# Register the custom filter with the app
app.jinja_env.filters['get_attribute'] = get_attribute

# Login Manager setup
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"

# Path to the static/uploads folder
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Directory of the current file
UPLOAD_FOLDER = os.path.join(BASE_DIR, '../static/uploads')  # Relative to the project root
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Import routes after app and db are initialized
from controllers import routes