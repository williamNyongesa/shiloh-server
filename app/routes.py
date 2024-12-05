from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt
from flask_restx import Namespace, Resource, reqparse
from datetime import datetime
from app import db
from app.models import Student, User, Teacher, Finance, Enrollment

# Initialize Bcrypt
bcrypt = Bcrypt()

# Namespaces
students_ns = Namespace('students', description='Student management operations')
users_ns = Namespace('users', description='User management operations')
teachers_ns = Namespace('teachers', description='Teacher management operations')
finances_ns = Namespace('finances', description='Finance management operations')
enrollments_ns = Namespace('enrollments', description='Enrollment management operations')

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

teacher_parser = reqparse.RequestParser()
teacher_parser.add_argument('name', type=str, required=True, help='Name of the teacher')
teacher_parser.add_argument('subject', type=str, required=True, help='Subject expertise of the teacher')
teacher_parser.add_argument('user_id', type=int, required=True, help='User ID for the teacher')

finance_parser = reqparse.RequestParser()
finance_parser.add_argument('student_id', type=int, required=True, help='ID of the student')
finance_parser.add_argument('amount', type=float, required=True, help='Amount of the transaction')
finance_parser.add_argument('description', type=str, required=True, help='Description of the transaction')

enrollment_parser = reqparse.RequestParser()
enrollment_parser.add_argument('student_id', type=int, required=True, help='Student ID')
enrollment_parser.add_argument('courses', type=str, required=True, help='Courses to enroll (comma-separated)')
enrollment_parser.add_argument('phone_number', type=str, required=True, help='Phone number')
enrollment_parser.add_argument('enrollment_date', type=datetime, required=False, help='Enrollment date (optional)')

# Student Routes
@students_ns.route('')
class StudentListResource(Resource):
    def get(self):
        students = Student.query.all()
        return [student.to_dict() for student in students], 200

    def post(self):
        data = student_parser.parse_args()
        new_student = Student.create_with_unique_id(
            name=data['name'],
            email=data['email'],
            phone_number=data['phone_number'],
            country_name=data['country_name']
        )
        return new_student.to_dict(), 201

@students_ns.route('/<int:student_id>')
class StudentResource(Resource):
    def get(self, student_id):
        student = Student.query.get_or_404(student_id)
        return student.to_dict(), 200

    def put(self, student_id):
        student = Student.query.get_or_404(student_id)
        data = student_parser.parse_args()
        student.name = data['name']
        student.email = data['email']
        student.phone_number = data['phone_number']
        db.session.commit()
        return student.to_dict(), 200

    def delete(self, student_id):
        student = Student.query.get_or_404(student_id)
        db.session.delete(student)
        db.session.commit()
        return '', 204

# User Routes
@users_ns.route('')
class UserListResource(Resource):
    def get(self):
        users = User.query.all()
        return [user.to_dict() for user in users], 200

    def post(self):
        data = user_parser.parse_args()
        new_user = User(email=data['email'], username=data['username'], role=data['role'])
        new_user.password = data['password']  # This will trigger the password setter
        db.session.add(new_user)
        db.session.commit()
        return new_user.to_dict(), 201  # Return the newly created user as a dictionary

@users_ns.route('/login')
class UserLoginResource(Resource):
    def post(self):
        data = login_parser.parse_args()  # Assuming login_parser exists to parse the login fields
        username = data['username']
        password = data['password']

        # Fetch the user from the database
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user._password, password):
            access_token = create_access_token(identity=user.id)
            return {
                'access_token': access_token,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }, 200
        else:
            return {'error': 'Invalid username or password'}, 401

# Teacher Routes
@teachers_ns.route('')
class TeacherListResource(Resource):
    def get(self):
        teachers = Teacher.query.all()
        return [teacher.to_dict() for teacher in teachers], 200

    def post(self):
        data = teacher_parser.parse_args()
        new_teacher = Teacher(name=data['name'], subject=data['subject'], user_id=data['user_id'])
        db.session.add(new_teacher)
        db.session.commit()
        return new_teacher.to_dict(), 201

# Finance Routes
@finances_ns.route('')
class FinanceListResource(Resource):
    def get(self):
        finances = Finance.query.all()
        return [finance.to_dict() for finance in finances], 200

    def post(self):
        data = finance_parser.parse_args()
        new_finance = Finance(student_id=data['student_id'], amount=data['amount'], description=data['description'])
        db.session.add(new_finance)
        db.session.commit()
        return new_finance.to_dict(), 201

# Enrollment Routes
@enrollments_ns.route('')
class EnrollmentListResource(Resource):
    def get(self):
        """Retrieve all enrollments"""
        enrollments = Enrollment.query.all()
        return [enrollment.to_dict() for enrollment in enrollments], 200

    def post(self):
        """Create a new enrollment"""
        data = enrollment_parser.parse_args()
        
        # Validate that the student exists
        student = Student.query.get(data['student_id'])
        if not student:
            return {'message': 'Student not found'}, 404
        
        # Validate required fields
        if not data['courses'] or not data['phone_number']:
            return {"message": "Missing required fields: courses or phone_number"}, 400

        try:
            # Create new enrollment record
            new_enrollment = Enrollment(
                student_id=data['student_id'],
                courses=data['courses'],
                phone_number=data['phone_number'],
                enrollment_date=data.get('enrollment_date', datetime.now())
            )
            db.session.add(new_enrollment)
            db.session.commit()
            return new_enrollment.to_dict(), 201
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            return {"message": f"Error saving enrollment: {str(e)}"}, 500

@enrollments_ns.route('/courses')
class EnrollmentCoursesResource(Resource):
    def get(self):
        """Retrieve unique list of courses"""
        try:
            enrollments = Enrollment.query.all()
            all_courses = set()  # Use a set to ensure uniqueness

            # Extract and collect all unique courses
            for enrollment in enrollments:
                all_courses.update(enrollment.courses.split(", "))

            return {"courses": list(all_courses)}, 200
        except Exception as e:
            return {"message": f"Error retrieving courses: {str(e)}"}, 500

