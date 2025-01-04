import pandas as pd
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from flask_bcrypt import Bcrypt
from flask_restx import Namespace, Resource, reqparse
from datetime import datetime
from app import db
from app.models import Attendance, FileUpload, Student, User, Teacher, Finance, Enrollment, Event, Quiz, Question, ClassSchedule, Invoice, Payment, Notification, Grade, send_sms
from marshmallow import ValidationError

from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest

import os
from io import BytesIO
from flask import request, jsonify, current_app
from sqlalchemy.exc import IntegrityError, OperationalError
from flask_mail import Mail, Message
from celery import Celery

# Initialize Celery
celery = Celery(__name__, broker='redis://localhost:6379/0')

# Define the send_email function
def send_email(recipient, subject, message):
    mail = Mail()
    msg = Message(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[recipient]
    )
    msg.body = message
    mail.send(msg)

# Define the send_sms function````
def send_sms(recipient, message):
    # Implement SMS sending logic here
    pass

# Celery task for sending email
@celery.task
def send_email_task(recipient, subject, message):
    send_email(recipient, subject, message)

# Celery task for sending SMS
@celery.task
def send_sms_task(recipient, message):
    send_sms(recipient, message)

import time

bcrypt = Bcrypt()

students_ns = Namespace('students', description='Student management operations')
users_ns = Namespace('users', description='User management operations')
teachers_ns = Namespace('teachers', description='Teacher management operations')
finances_ns = Namespace('finances', description='Finance management operations')
enrollments_ns = Namespace('enrollments', description='Enrollment management operations')
quizzes_ns = Namespace('quizzes', description='Quiz management operations')
events_ns = Namespace('events', description='Event related operations')
fees_ns = Namespace('fees', description='Fee management operations')
timetable_ns = Namespace('timetable', description='Timetable scheduling operations')
communication_ns = Namespace('communication', description='Communication tools operations')
reporting_ns = Namespace('reporting', description='Advanced reporting operations')
grades_ns = Namespace('grades', description='Grade management operations')

student_parser = reqparse.RequestParser()
student_parser.add_argument('first_name', type=str, required=True, help='First Name of the student')
student_parser.add_argument('middle_name', type=str, required=False, help='Middle Name of the student')
student_parser.add_argument('last_name', type=str, required=True, help='Last Name of the student')
student_parser.add_argument('name', type=str, required=True, help='Name of the student')
student_parser.add_argument('email', type=str, required=True, help='Email of the student')
student_parser.add_argument('phone_number', type=str, required=True, help='Phone number of the student')
student_parser.add_argument('country_name', type=str, required=True, help='Country of the student')
user_parser = reqparse.RequestParser()
user_parser.add_argument('email', type=str, required=False, help='Email of the user')
user_parser.add_argument('username', type=str, required=False, help='Username of the user')
user_parser.add_argument('password', type=str, required=False, help='Password of the user')
user_parser.add_argument('role', type=str, required=False, help='Role of the user')

# user_parser = reqparse.RequestParser()
# user_parser.add_argument('email', type=str, required=True, help='Email of the user')
# user_parser.add_argument('username', type=str, required=True, help='Username of the user')
# user_parser.add_argument('password', type=str, required=True, help='Password of the user')

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
enrollment_parser.add_argument('email', type=str, required=True, help="Email is required")
enrollment_parser.add_argument('courses', type=str, required=True, help='Courses to enroll (comma-separated)')
enrollment_parser.add_argument('phone_number', type=str, required=True, help='Phone number')
enrollment_parser.add_argument('enrollment_date', type=datetime, required=False, help='Enrollment date (optional)')

quiz_parser = reqparse.RequestParser()
quiz_parser.add_argument('title', type=str, required=True, help='Title of the quiz')

question_parser = reqparse.RequestParser()
question_parser.add_argument('text', type=str, required=True, help='Text of the question')
question_parser.add_argument('options', type=str, required=True, help='Comma-separated options for the question')
question_parser.add_argument('correct_answer', type=str, required=True, help='Correct answer for the question')

grade_parser = reqparse.RequestParser()
grade_parser.add_argument('student_id', type=int, required=True, help='Student ID')
grade_parser.add_argument('course', type=str, required=True, help='Course name')
grade_parser.add_argument('grade', type=str, required=True, help='Grade')

# def is_admin():
#     user_id = get_jwt_identity()  
#     user = User.query.get(user_id)  
#     return user and user.role == 'admin'
def is_admin():
    claims = get_jwt_identity()  # Get all claims from the JWT token
    print(claims)
    return claims.get('role') == 'admin'

def send_welcome_email(user):
    mail = Mail()
    msg = Message(
        subject="Welcome to Shiloh Project",
        sender="noreply@shilohproject.com",
        recipients=[user.email]
    )
    msg.body = f"Hello {user.username},\n\nWelcome to Shiloh Project! We're excited to have you on board."
    mail.send(msg)
@students_ns.route('')
class StudentListResource(Resource):
    def get(self):
        students = Student.query.all()
        return [student.to_dict() for student in students], 200

    def post(self):
        data = request.get_json()
        if not data:
            return {"message": "Invalid JSON or empty body"}, 400

        first_name = data.get('first_name')
        middle_name = data.get('middle_name')
        last_name=data.get('last_name')
        phone_number = data.get('phone_number')
        email = data.get('email')
        country_name = data.get('country_name')
        password=data.get('password')
        print(data)

        required_fields = ["first_name", "middle_name", "last_name", "phone_number", "email", "country_name", "password"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return {
                "message": "Missing required fields",
                "missing_fields": missing_fields,
                "provided_data": data
            }, 400


        existing_student_by_email = Student.query.filter_by(email=email).first()
        existing_student_by_phone = Student.query.filter_by(phone_number=phone_number).first()

        if existing_student_by_email:
            return {'message': 'Student with this email already exists.'}, 400
        if existing_student_by_phone:
            return {'message': 'Student with this phone number already exists.'}, 400

        try:
            new_student = Student.create_with_unique_id(first_name, middle_name, last_name, phone_number, email, country_name, password)
            return new_student.to_dict(), 201
        except ValidationError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            return {'message': str(e)}, 500

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

    @jwt_required()
    def delete(self, student_id):
        student = Student.query.get_or_404(student_id)
        if not is_admin():
            return {"message": "Admin privileges required."}, 403  # Forbidden
        db.session.delete(student)
        db.session.commit()
        return '', 204


@users_ns.route('')
class UserListResource(Resource):
    def get(self):
        users = User.query.all()
        return [user.to_dict() for user in users], 200

    def post(self):
        data = user_parser.parse_args()
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if not email or not username or not password:
            return {'message': 'Missing required fields'}, 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return {'message': 'User with this email already exists.'}, 400

        new_user = User(email=email, username=username, role='user')
        new_user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.add(new_user)
        db.session.commit()

        # send_welcome_email(new_user)

        return new_user.to_dict(), 201


    @jwt_required() 
    def put(self):
        email = get_jwt_identity()
        data = user_parser.parse_args()
        user = User.query.filter_by(email=email).first() 
        
        if not user:
            return {'error': 'User not found'}, 404
       
        if 'email' in data:
            user.email = data['email']
        if 'password' in data:
            user.password = data['password'] 
        
        try:
            db.session.commit()
            return user.to_dict(), 200
        except ValidationError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            return {'error': 'Failed to update user data'}, 500
        
@users_ns.route('/refresh')
class TokenRefreshResource(Resource):
    @jwt_required(refresh=True)
    def post(self):
        try:
            current_user = get_jwt_identity()
            new_access_token = create_access_token(identity=current_user)
            return {'access_token': new_access_token}, 200
        except Exception:
            return {'message': 'Token is expired or invalid'}, 401
        
@users_ns.route('/logout')
class UserLogoutResource(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt_identity()
        # Here you would add the token to a blacklist or perform other logout operations
        return {'message': 'Successfully logged out'}, 200
    


@users_ns.route('/login')
class UserLoginResource(Resource):
    def post(self):
        data = login_parser.parse_args()
        email = data['email']
        password = data['password']
        
        # Fetch the user by username
        user = User.query.filter_by(username=email).first()
        if user and bcrypt.check_password_hash(user._password, password):
            # Generate both access token and refresh token
            access_token = create_access_token(identity=user.id, additional_claims={"role": user.role})
            refresh_token = create_refresh_token(identity=user.id)
            
            response = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'username': user.username,
                'email': user.email,
                'role': user.role,
            }
            
            # Check if the user is a student and add the student data if role is "student"
            if user.role == 'student':
                student = Student.query.filter_by(email=user.email).first()
                if student:
                    # Include student data in the response
                    response['student'] = student.to_dict()
            
            # Check if the user is a teacher and add the teacher data if role is "teacher"
            if user.role == 'teacher':
                teacher = Teacher.query.filter_by(user_id=user.id).first()
                if teacher:
                    # Include teacher data in the response
                    response['teacher'] = teacher.to_dict()
            
            return response, 200
        else:
            return {'error': 'Invalid username or password'}, 401




@users_ns.route('/<int:user_id>')
class UserResource(Resource):
    @jwt_required()
    def get(self, user_id):
        # Fetch the user or return a 404 error if the user does not exist
        user = User.query.get_or_404(user_id, "User does not exist")
        
        # Create the base response with user data
        response = {
            'user': user.to_dict()  # Convert the user object to a dictionary
        }

        # Add role-specific data
        if user.role == 'student':
            student = Student.query.filter_by(email=user.email).first()
            if student:
                response['role_data'] = {
                    'role': 'student',
                    'details': student.to_dict()  # Convert student object to dictionary
                }
        
        elif user.role == 'teacher':
            teacher = Teacher.query.filter_by(user_id=user.id).first()
            if teacher:
                response['role_data'] = {
                    'role': 'teacher',
                    'details': teacher.to_dict()  # Convert teacher object to dictionary
                }

        return response, 200

        

    # @jwt_required()
    def put(self, user_id):
        user = User.query.get_or_404(user_id)
        data = user_parser.parse_args()
        if 'username' in data:
            user.username = data['username']
        
        if 'email' in data:
            user.email = data['email']
        
        if 'role' in data:
            user.role = data['role']
        if 'password' in data and data['password']:
            user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        try:
            db.session.commit()
            return user.to_dict(), 200
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update user: {str(e)}'}, 500


    @jwt_required()
    def delete(self, user_id):
        user = User.query.get_or_404(user_id)
        
        # Check if the user is referenced by any students
        students = Student.query.filter_by(user_id=user_id).all()
        for student in students:
            # Check if the student is referenced by any finances
            finances = Finance.query.filter_by(student_id=student.id).all()
            for finance in finances:
                db.session.delete(finance)
            db.session.delete(student)
        
        # Check if the user is referenced by any teachers
        teachers = Teacher.query.filter_by(user_id=user_id).all()
        for teacher in teachers:
            db.session.delete(teacher)
        
        # Check if the user is referenced by any enrollments
        enrollments = Enrollment.query.filter_by(student_id=user_id).all()
        for enrollment in enrollments:
            db.session.delete(enrollment)
        
        db.session.delete(user)
        db.session.commit()
        return '', 204


@teachers_ns.route('')
class TeacherListResource(Resource):
    # @jwt_required()
    def get(self):
        teachers = Teacher.query.all()
        return [teacher.to_dict() for teacher in teachers], 200
    
    @jwt_required()
    def post(self):
        data = teacher_parser.parse_args()
        new_teacher = Teacher(name=data['name'], subject=data['subject'], user_id=data['user_id'])
        db.session.add(new_teacher)
        db.session.commit()
        return new_teacher.to_dict(), 201

@teachers_ns.route('/<int:teacher_id>')
class TeacherResource(Resource):
    # @jwt_required()  # Uncomment this if JWT authentication is required
    def get(self, teacher_id):
        """Get a teacher by their ID."""
        teacher = Teacher.query.get(teacher_id)
        if teacher:
            return teacher.to_dict(), 200
        else:
            return {"message": "Teacher not found"}, 404


@finances_ns.route('')
class FinanceListResource(Resource):

    # @jwt_required()   
    def get(self):
        finances = Finance.query.all()
        return [finance.to_dict() for finance in finances], 200
    
    @jwt_required()
    def post(self):
        data = finance_parser.parse_args()
        new_finance = Finance(student_id=data['student_id'], amount=data['amount'], description=data['description'])
        db.session.add(new_finance)
        db.session.commit()
        return new_finance.to_dict(), 201

@enrollments_ns.route('')
class EnrollmentListResource(Resource):
    def get(self):
        enrollments = Enrollment.query.all()
        return [enrollment.to_dict() for enrollment in enrollments], 200

    def post(self):
        data = enrollment_parser.parse_args()
        student = Student.query.filter_by(email=data['email']).first()
        if not student:
            return {'message': 'Student not found'}, 404

        if not data['courses'] or not data['phone_number']:
            return {"message": "Missing required fields: courses or phone_number"}, 400

        document = request.files.get('document_file')
        if not document:
            return {"message": "Missing document file"}, 400

        try:
            allowed_extensions = {'pdf', 'docx', 'pptx'}
            if '.' not in document.filename or document.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                return {"message": "Invalid file type, allowed types are: pdf, docx, pptx"}, 400

            filename = secure_filename(document.filename)
            file_data = document.read()
            courses = data['courses']

            new_enrollment = Enrollment(
                student_id=student.id,
                courses=courses,
                phone_number=data['phone_number'],
                enrollment_date=data.get('enrollment_date', datetime.now()),
                document_file=file_data
            )

            db.session.add(new_enrollment)
            db.session.commit()
            return new_enrollment.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            return {"message": f"Error saving enrollment with document: {str(e)}"}, 500

@enrollments_ns.route('/courses')
class EnrollmentCoursesResource(Resource):
    def get(self):
        try:
            enrollments = Enrollment.query.all()
            all_courses = set()
            for enrollment in enrollments:
                all_courses.update(enrollment.courses.split(", "))
            return {"courses": list(all_courses)}, 200
        except Exception as e:
            return {"message": f"Error retrieving courses: {str(e)}"}, 500

@quizzes_ns.route('')
class QuizListResource(Resource):
    # @jwt_required()
    def get(self):
        quizzes = Quiz.query.all()
        quiz_list = []
        for quiz in quizzes:
            questions = [{'id': q.id, 'text': q.text, 'options': q.options.split(', ')} for q in quiz.questions]
            quiz_list.append({'id': quiz.id, 'title': quiz.title, 'questions': questions})
        return jsonify({'quizzes': quiz_list})

    # @jwt_required()
    def post(self):
        data = quiz_parser.parse_args()
        try:
            new_quiz = Quiz(title=data['title'])
            db.session.add(new_quiz)
            db.session.commit()
            quiz_id = new_quiz.id
            quiz = Quiz.query.get_or_404(quiz_id)

            questions = request.json.get('questions', [])
            for question_data in questions:
                new_question = Question(
                    text=question_data['text'],
                    options=', '.join(question_data['options']),
                    correct_answer=question_data.get('correct_answer', ''),
                    quiz_id=quiz.id
                )
                db.session.add(new_question)
            
            db.session.commit()
            return {'message': 'Quiz created', 'quiz': quiz.to_dict()}, 201
        except Exception as e:
            db.session.rollback()
            # Log the error
            current_app.logger.error(f'Error creating quiz: {str(e)}')
            return {'message': f'Error creating quiz: {str(e)}'}, 500
        
    def put(self, quiz_id):
        data = quiz_parser.parse_args()
        quiz = Quiz.query.get_or_404(quiz_id)
        quiz.title = data['title']

        try:
            questions = request.json.get('questions', [])
            for question_data in questions:
                question = Question.query.filter_by(id=question_data['id'], quiz_id=quiz.id).first()
                if question:
                    question.text = question_data['text']
                    question.options = ', '.join(question_data['options'])
                    question.correct_answer = question_data.get('correct_answer', '')
                else:
                    new_question = Question(
                        text=question_data['text'],
                        options=', '.join(question_data['options']),
                        correct_answer=question_data.get('correct_answer', ''),
                        quiz_id=quiz.id
                    )
                    db.session.add(new_question)
            
            db.session.commit()
            return {'message': 'Quiz updated', 'quiz': quiz.to_dict()}, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating quiz: {str(e)}')
            return {'message': f'Error updating quiz: {str(e)}'}, 500

@quizzes_ns.route('/<int:quiz_id>')
class QuizResource(Resource):
    def put(self, quiz_id):
        data = quiz_parser.parse_args()
        quiz = Quiz.query.get_or_404(quiz_id)
        quiz.title = data['title']

        try:
            questions = request.json.get('questions', [])
            for question_data in questions:
                question_id = question_data.get('id')
                if question_id:
                    question = Question.query.filter_by(id=question_id, quiz_id=quiz.id).first()
                    if question:
                        question.text = question_data['text']
                        question.options = ', '.join(question_data['options'])
                        question.correct_answer = question_data.get('correct_answer', '')
                    else:
                        new_question = Question(
                            text=question_data['text'],
                            options=', '.join(question_data['options']),
                            correct_answer=question_data.get('correct_answer', ''),
                            quiz_id=quiz.id
                        )
                        db.session.add(new_question)
                else:
                    new_question = Question(
                        text=question_data['text'],
                        options=', '.join(question_data['options']),
                        correct_answer=question_data.get('correct_answer', ''),
                        quiz_id=quiz.id
                    )
                    db.session.add(new_question)
            
            db.session.commit()
            return {'message': 'Quiz updated', 'quiz': quiz.to_dict()}, 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating quiz: {str(e)}')
            return {'message': f'Error updating quiz: {str(e)}'}, 500

@quizzes_ns.route('/<int:quiz_id>/questions')
class QuizQuestionListResource(Resource):
    def get(self, quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        questions = [{'id': q.id, 'text': q.text, 'options': q.options.split(', ')} for q in quiz.questions]
        return jsonify({'quiz_id': quiz.id, 'questions': questions})

    def post(self, quiz_id):
        data = question_parser.parse_args()
        quiz = Quiz.query.get_or_404(quiz_id)

        try:
            new_question = Question(
                text=data['text'],
                options=data['options'],
                correct_answer=data['correct_answer'],
                quiz_id=quiz.id
            )
            db.session.add(new_question)
            db.session.commit()
            return jsonify({'message': 'Question added', 'question': new_question.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error adding question: {str(e)}'}, 500

@quizzes_ns.route('/submit-quiz', methods=['POST'])
class SubmitQuizResource(Resource):
    def post(self):
        data = request.get_json()
        if not data:
            return {'message': 'Invalid JSON or empty body'}, 400

        quiz_id = data.get('quiz_id')
        student_id = data.get('student_id')
        answers = data.get('answers')

        if not quiz_id or not student_id or not answers:
            return {'message': 'Missing required fields'}, 400

        quiz = Quiz.query.get_or_404(quiz_id)
        student = Student.query.get_or_404(student_id)

        total_questions = len(quiz.questions)
        correct_answers = sum(1 for answer in answers if answer['selected_option'] == answer['correct_option'])

        score = (correct_answers / total_questions) * 100
        return {'student_id': student.id, 'quiz_id': quiz.id, 'score': score}, 200
    


# Helper function to validate and save the file
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'xls', 'xlsx', 'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@users_ns.route('/upload')
class FileUploadResource(Resource):
    # @jwt_required()  # Optional: Only allow authenticated users to upload
    def post(self):
        # Check if a file is part of the request
        if 'file' not in request.files:
            return {"message": "No file part in the request"}, 400
        
        file = request.files['file']
        
        # If no file is selected or file is empty
        if file.filename == '':
            return {"message": "No selected file"}, 400

        # Validate file extension
        if not allowed_file(file.filename):
            return {"message": "Invalid file type. Only .xls, .xlsx, and .csv are allowed"}, 400

        # Secure the filename and read file data
        filename = secure_filename(file.filename)
        file_type = filename.rsplit('.', 1)[1].lower()  # Get the file extension (type)
        
        # Read the file data into memory as binary
        file_data = file.read()  # Store the file's content in binary form

        try:
            # Create a new FileUpload instance to store the file data
            new_file = FileUpload(filename=filename, file_type=file_type, file_data=file_data)
            
            # Add the new file record to the database session
            db.session.add(new_file)
            db.session.commit()
            file.close()
            return {"message": f"File '{filename}' uploaded successfully."}, 201

        except Exception as e:
            db.session.rollback()  # Rollback the transaction if there's an error
            return {"message": f"Error processing file: {str(e)}"}, 500

def retry_on_operational_error(retries=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if attempt < retries - 1:
                        time.sleep(delay)
                    else:
                        raise e
        return wrapper
    return decorator

# Apply the retry decorator to the route handler
class TeacherResource(Resource):
    @jwt_required()
    @retry_on_operational_error()
    def get(self):
        teachers = Teacher.query.all()
        return jsonify(teachers)

@fees_ns.route('/invoices')
class InvoiceResource(Resource):
    def get(self):
        invoices = Invoice.query.all()
        return [invoice.to_dict() for invoice in invoices], 200

    def post(self):
        data = request.get_json()
        new_invoice = Invoice(
            student_id=data['student_id'],
            amount=data['amount'],
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d'),
            status=data.get('status', 'unpaid')
        )
        db.session.add(new_invoice)
        db.session.commit()
        return new_invoice.to_dict(), 201

@fees_ns.route('/payments')
class PaymentResource(Resource):
    def get(self):
        payments = Payment.query.all()
        return [payment.to_dict() for payment in payments], 200

    def post(self):
        data = request.get_json()
        new_payment = Payment(
            invoice_id=data['invoice_id'],
            amount=data['amount'],
            payment_date=datetime.strptime(data['payment_date'], '%Y-%m-%d')
        )
        db.session.add(new_payment)
        db.session.commit()
        return new_payment.to_dict(), 201

@timetable_ns.route('/classes')
class ClassScheduleResource(Resource):
    def get(self):
        schedules = ClassSchedule.query.all()
        return [schedule.to_dict() for schedule in schedules], 200

    def post(self):
        data = request.get_json()
        new_schedule = ClassSchedule(
            class_name=data['class_name'],
            room_number=data['room_number'],
            start_time=datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S'),
            end_time=datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
        )
        db.session.add(new_schedule)
        db.session.commit()
        return new_schedule.to_dict(), 201

@communication_ns.route('/notifications')
class NotificationResource(Resource):
    @retry_on_operational_error()
    def get(self):
        # Fetch all notifications from the database
        notifications = Notification.query.all()
        return [notification.to_dict() for notification in notifications], 200

    @retry_on_operational_error()
    def post(self):
        data = request.get_json()
        notification_type = data['type']
        subject = data.get('subject', 'Notification')
        message = data['message']

        # Fetch all users
        users = User.query.all()
        recipients = [user.email for user in users]

        if notification_type == 'email':
            for recipient in recipients:
                send_email_task.delay(recipient, subject, message)
        elif notification_type == 'sms':
            for recipient in recipients:
                send_sms_task.delay(recipient, message)
        else:
            return {'message': 'Invalid notification type'}, 400

        # Save the notification to the database
        new_notification = Notification(type=notification_type, subject=subject, message=message)
        db.session.add(new_notification)
        db.session.commit()

        return {'message': 'Notifications sent'}, 200

@reporting_ns.route('/analytics')
class AnalyticsResource(Resource):
    def get(self):
        # Implement analytics logic here
        return {'message': 'Analytics data'}, 200

@grades_ns.route('')
class GradeListResource(Resource):
    def get(self):
        grades = Grade.query.all()
        return [grade.to_dict() for grade in grades], 200

    def post(self):
        data = grade_parser.parse_args()
        new_grade = Grade(
            student_id=data['student_id'],
            course=data['course'],
            grade=data['grade']
        )
        db.session.add(new_grade)
        db.session.commit()
        return new_grade.to_dict(), 201

@grades_ns.route('/<int:grade_id>')
class GradeResource(Resource):
    def get(self, grade_id):
        grade = Grade.query.get_or_404(grade_id)
        return grade.to_dict(), 200

    def put(self, grade_id):
        grade = Grade.query.get_or_404(grade_id)
        data = grade_parser.parse_args()
        grade.course = data['course']
        grade.grade = data['grade']
        db.session.commit()
        return grade.to_dict(), 200

    def delete(self, grade_id):
        grade = Grade.query.get_or_404(grade_id)
        db.session.delete(grade)
        db.session.commit()
        return '', 204

    def post(self):
        data = grade_parser.parse_args()
        student_id=data['student_id']

        new_grade = Grade(
            student_id,
            user_name=data['username'],
            course=data['course'],
            grade=data['grade']
        )
        db.session.add(new_grade)
        db.session.commit()
        return new_grade.to_dict(), 201
attendance_ns = Namespace('attendance', description='Attendance Management')

attendance_parser = reqparse.RequestParser()
attendance_parser.add_argument('student_id', type=int, required=True, help='Student ID is required')
attendance_parser.add_argument('status', type=str, required=True, choices=('Present', 'Absent', 'Late'), help='Status is required')
attendance_parser.add_argument('course', type=str, required=True, help='Course is required')  # Add this line


report_parser = reqparse.RequestParser()
report_parser.add_argument('start_date', type=str, required=False, help='Start date in YYYY-MM-DD format')
report_parser.add_argument('end_date', type=str, required=False, help='End date in YYYY-MM-DD format')

@attendance_ns.route('')
class AttendanceResource(Resource):
    def post(self):
        """Mark attendance for a student by course."""
        data = attendance_parser.parse_args()

        # Validate if the student is enrolled in the specified course
        student_id = data['student_id']
        course = data['course']

        enrollment = Enrollment.query.filter_by(student_id=student_id).filter(Enrollment.courses.contains(course)).first()
        if not enrollment:
            return {'message': f'Student ID {student_id} is not enrolled in course {course}'}, 404

        try:
            attendance = Attendance(
                student_id=student_id,
                course=course,
                date=datetime.utcnow().date(),
                status=data['status']
            )
            db.session.add(attendance)
            db.session.commit()
            return {'message': 'Attendance marked', 'attendance': attendance.to_dict()}, 201
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error marking attendance: {str(e)}'}, 500


@attendance_ns.route('/report')
class AttendanceReportResource(Resource):
    def get(self):
        """Generate attendance reports within a specified date range."""
        args = reqparse.RequestParser()
        args.add_argument('start_date', type=str, required=False, help="Start date in 'YYYY-MM-DD' format.")
        args.add_argument('end_date', type=str, required=False, help="End date in 'YYYY-MM-DD' format.")
        parsed_args = args.parse_args()

        start_date = (
            datetime.strptime(parsed_args.get('start_date'), '%Y-%m-%d') 
            if parsed_args.get('start_date') else None
        )
        end_date = (
            datetime.strptime(parsed_args.get('end_date'), '%Y-%m-%d') 
            if parsed_args.get('end_date') else None
        )

        query = Attendance.query
        if start_date:
            query = query.filter(Attendance.date >= start_date)
        if end_date:
            query = query.filter(Attendance.date <= end_date)

        attendance_records = query.all()
        return [record.to_dict() for record in attendance_records], 200


@attendance_ns.route('/students_by_course')
class StudentsByCourseResource(Resource):
    def get(self):
        """Get all students who have attendance records for a specific course."""
        args = reqparse.RequestParser()
        args.add_argument('course', type=str, required=True, help="Course name is required.")
        parsed_args = args.parse_args()
        course_name = parsed_args.get('course')

        # Fetch attendance records for the specific course
        attendance_records = Attendance.query.filter(Attendance.course.ilike(f'%{course_name}%')).all()
        
        # Extract unique student IDs from attendance records
        student_ids = {record.student_id for record in attendance_records}

        # Query students by the extracted IDs
        students = Student.query.filter(Student.id.in_(student_ids)).all()

        # Return the student data as a list of dictionaries
        return [student.to_dict() for student in students], 200
