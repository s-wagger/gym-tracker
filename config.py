import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask & Database Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'gym-tracker-dev-key-12345')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///gym_tracker.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email OTP Configuration (Gmail SMTP)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')