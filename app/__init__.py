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
from celery import Celery
from flask_mail import Mail

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
api = Api()
migrate = Migrate()
mail = Mail()

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

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
    mail.init_app(app)  # Initialize Flask-Mail

    # Configure JWT
    app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = Config.JWT_ACCESS_TOKEN_EXPIRES
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = Config.JWT_REFRESH_TOKEN_EXPIRES

    # Apply CORS to the app
    CORS(app)

    app.config.update(
        CELERY_BROKER_URL='redis://localhost:6379/0',
        CELERY_RESULT_BACKEND='redis://localhost:6379/0'
    )

    celery = make_celery(app)

    # Register namespaces
    from app.routes import (
        students_ns,
        users_ns,
        teachers_ns,
        finances_ns,
        enrollments_ns,
        events_ns,
        quizzes_ns,
        fees_ns,
        timetable_ns,
        communication_ns,
        reporting_ns,
        grades_ns,  # Add grades namespace
    )

    api.add_namespace(students_ns, path='/students')
    api.add_namespace(users_ns, path='/users')
    api.add_namespace(teachers_ns, path='/teachers')
    api.add_namespace(finances_ns, path='/finances')
    api.add_namespace(enrollments_ns, path='/enrollments')
    api.add_namespace(events_ns, path='/events')
    api.add_namespace(quizzes_ns, path='/quizzes')  # Corrected path
    api.add_namespace(fees_ns)
    api.add_namespace(timetable_ns)
    api.add_namespace(communication_ns)
    api.add_namespace(reporting_ns)
    api.add_namespace(grades_ns, path='/grades')  # Register grades namespace

    return app, celery

# Create the application instance
app, celery = create_app()
