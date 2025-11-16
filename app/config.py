import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv() # This line reads your .env file and loads the variables

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Configuration class that loads settings from the environment.
    """
    # General Flask Config
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application. This is a critical security risk.")
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("No DATABASE_URI set for Flask application.")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = True 

    # Twilio Config
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    if not TWILIO_ACCOUNT_SID:
        raise ValueError("No TWILIO_ACCOUNT_SID set.")
    
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

    # File Content (MIME) Validation
    # This prevents uploading a .jpg that is actually an HTML/script file.
    ALLOWED_MIME_TYPES = [
        'application/pdf',
        'image/png',
        'image/jpeg',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document' # .docx
    ]

    MAX_CONTENT_LENGTH = 18 * 1024 * 1024