from datetime import datetime, timedelta
from flask_restx import Namespace, Resource, reqparse
from flask_jwt_extended import create_access_token
from app import db
from app.models import Student, User

# Namespaces
students_ns = Namespace('students', description='Student management operations')
users_ns = Namespace('users', description='User management operations')

# Parsers
student_parser = reqparse.RequestParser()
student_parser.add_argument('name', type=str, required=True, help='Name of the student')
student_parser.add_argument('email', type=str, required=True, help='Email of the student')
student_parser.add_argument('phone_number', type=str, required=True, help='Phone number of the student')
student_parser.add_argument('country_name', type=str, required=True, help='Country of the student')

user_parser = reqparse.RequestParser()
user_parser.add_argument('email', type=str, required=True, help='Email of the user')
user_parser.add_argument('username', type=str, required=True, help='Username of the user')
user_parser.add_argument('role', type=str, required=True, help='Role of the user')
user_parser.add_argument('password', type=str, required=True, help='Password of the user')

login_parser = reqparse.RequestParser()
login_parser.add_argument('username', type=str, required=True, help='Username for login')
login_parser.add_argument('password', type=str, required=True, help='Password for login')

# Student routes
@students_ns.route('', endpoint='students')
class StudentListResource(Resource):
    def get(self):
        """Retrieve a list of students."""
        students = Student.query.all()
        return [student.to_dict() for student in students], 200

    def post(self):
        """Create a new student."""
        data = student_parser.parse_args()
        
        # Create a new student with a unique ID
        new_student = Student.create_with_unique_id(
            name=data['name'],
            phone_number=data['phone_number'],
            email=data['email'],
            country_name=data['country_name']
        )
        return new_student.to_dict(), 201

@students_ns.route('/<int:student_id>', endpoint='students/<int:student_id>')
class StudentResource(Resource):
    def get(self, student_id):
        """Retrieve a student by ID."""
        student = Student.query.get_or_404(student_id)
        return student.to_dict(), 200

    def put(self, student_id):
        """Update a student by ID."""
        student = Student.query.get_or_404(student_id)
        data = student_parser.parse_args()
        student.name = data['name']
        student.email = data['email']
        student.phone_number = data['phone_number']

        db.session.commit()
        return student.to_dict(), 200

    def delete(self, student_id):
        """Delete a student by ID."""
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
        return '', 204

# User routes
@users_ns.route('', endpoint='users')
class UserListResource(Resource):
    def get(self):
        """Retrieve a list of users."""
        users = User.query.all()
        return [user.to_dict() for user in users], 200

    def post(self):
        """Create a new user."""
        data = user_parser.parse_args()
        
        # Create a new user instance
        new_user = User(
            email=data['email'],
            username=data['username'],
            role=data['role']
        )
        new_user.password = data['password']  # Hash and set password

        db.session.add(new_user)
        db.session.commit()
        return new_user.to_dict(), 201

@users_ns.route('/<int:user_id>', endpoint='users/<int:user_id>')
class UserResource(Resource):
    def get(self, user_id):
        """Retrieve a user by ID."""
        user = User.query.get_or_404(user_id)
        return user.to_dict(), 200

    def put(self, user_id):
        """Update a user by ID."""
        user = User.query.get_or_404(user_id)
        data = user_parser.parse_args()
        
        user.email = data['email']
        user.username = data['username']
        user.role = data['role']
        
        if data.get('password'):
            user.password = data['password']  # Hash and set new password if provided
        
        db.session.commit()
        return user.to_dict(), 200

    def delete(self, user_id):
        """Delete a user by ID."""
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return '', 204

@users_ns.route('/login', endpoint='login')
class UserLoginResource(Resource):
    def post(self):
        """Authenticate user and return a JWT."""
        data = login_parser.parse_args()
        user = User.query.filter_by(username=data['username']).first()

        if not user or not user.check_password(data['password']):
            return {'message': 'Invalid username or password'}, 401
        
        access_token = create_access_token(identity=user.id)
        return {'access_token': access_token}, 200
