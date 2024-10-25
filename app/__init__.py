from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_restx import Api
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

    from app.routes import students_ns
    api.add_namespace(students_ns)

    
    return app

app = create_app()