from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

# Redirect unauthorized users to the login route
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'