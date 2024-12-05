from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_restx import Api
from flask_cors import CORS
from app.config import Config
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
api = Api()
migrate = Migrate()

def create_app():
    """Application factory for setting up the Flask app."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    api.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # Apply CORS to the app
    origins = os.getenv("CORS_FILTER", "").split(",")  # Ensure a default value if the variable isn't set
    CORS(
        app,
        origins=origins,
        supports_credentials=True,
    )

    # Register namespaces
    from app.routes import (
        students_ns,
        users_ns,
        teachers_ns,
        finances_ns,
        enrollments_ns,
    )

    api.add_namespace(students_ns, path='/students')
    api.add_namespace(users_ns, path='/users')
    api.add_namespace(teachers_ns, path='/teachers')
    api.add_namespace(finances_ns, path='/finances')
    api.add_namespace(enrollments_ns, path='/enrollments')

    return app

# Create the application instance
app = create_app()
