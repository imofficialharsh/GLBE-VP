from flask import Flask
from .config import Config
from .models import db
from .auth.routes import auth_bp
from .main.routes import main_bp
from .admin.routes import admin_bp
from datetime import datetime
import json
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()


def create_app():
    """
    Creates and configures an instance of the Flask application.
    """
    app = Flask(__name__, static_folder='static')
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)

    def from_json(json_string):
        if json_string:
            return json.loads(json_string)
        return []

    app.jinja_env.filters['fromjson'] = from_json
    
    @app.context_processor
    def inject_global_data():
        """This makes 'current_year' available in all templates."""
        return dict(current_year=datetime.utcnow().year)

    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')  # NEW: Register admin blueprint

    return app