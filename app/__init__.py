from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_restx import Api
from flask_cors import CORS
from app.config import Config


db = SQLAlchemy()

jwt = JWTManager()
bcrypt = Bcrypt()
api = Api()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    api.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # Apply CORS to the app
    CORS(app, origins=["http://localhost:3000","http://localhost:3001"], supports_credentials=True)

    from app.routes import students_ns, users_ns, teachers_ns,finances_ns
    api.add_namespace(students_ns)
    api.add_namespace(users_ns)
    api.add_namespace(teachers_ns)
    api.add_namespace(finances_ns)

    
    return app

app = create_app()