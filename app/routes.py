from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt
from flask_restx import Namespace, Resource, reqparse
from datetime import datetime
from app import db
from app.models import Student, User, Teacher, Finance, Enrollment, Event, Quiz, Question

from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest

import os
from io import BytesIO
from flask import request, jsonify
from sqlalchemy.exc import IntegrityError

bcrypt = Bcrypt()

students_ns = Namespace('students', description='Student management operations')
users_ns = Namespace('users', description='User management operations')
teachers_ns = Namespace('teachers', description='Teacher management operations')
finances_ns = Namespace('finances', description='Finance management operations')
enrollments_ns = Namespace('enrollments', description='Enrollment management operations')
quizzes_ns = Namespace('quizzes', description='Quiz management operations')
events_ns = Namespace('events', description='Event related operations')

student_parser = reqparse.RequestParser()
student_parser.add_argument('name', type=str, required=True, help='Name of the student')
student_parser.add_argument('email', type=str, required=True, help='Email of the student')
student_parser.add_argument('phone_number', type=str, required=True, help='Phone number of the student')
student_parser.add_argument('country_name', type=str, required=True, help='Country of the student')

user_parser = reqparse.RequestParser()
user_parser.add_argument('email', type=str, required=True, help='Email of the user')
user_parser.add_argument('username', type=str, required=True, help='Username of the user')
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

@students_ns.route('')
class StudentListResource(Resource):
    def get(self):
        students = Student.query.all()
        return [student.to_dict() for student in students], 200

    def post(self):
        data = request.get_json()
        if not data:
            return {"message": "Invalid JSON or empty body"}, 400

        name = data.get('name')
        phone_number = data.get('phone_number')
        email = data.get('email')
        country_name = data.get('country')

        if not all([name, phone_number, email, country_name]):
            return {"message": "Missing required fields"}, 400

        existing_student_by_email = Student.query.filter_by(email=email).first()
        existing_student_by_phone = Student.query.filter_by(phone_number=phone_number).first()

        if existing_student_by_email:
            return {'message': 'Student with this email already exists.'}, 400
        if existing_student_by_phone:
            return {'message': 'Student with this phone number already exists.'}, 400

        try:
            new_student = Student.create_with_unique_id(name, phone_number, email, country_name)
            return new_student.to_dict(), 201
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

    def delete(self, student_id):
        student = Student.query.get_or_404(student_id)
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
        new_user = User(email=data['email'], username=data['username'], role='user')
        new_user.password = data['password']
        db.session.add(new_user)
        db.session.commit()
        return new_user.to_dict(), 201

@users_ns.route('/login')
class UserLoginResource(Resource):
    def post(self):
        data = login_parser.parse_args()
        username = data['username']
        password = data['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user._password, password):
            access_token = create_access_token(identity=user.id)
            return {
                'access_token': access_token,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'user_profile_picture':user.user_profile_picture,
            }, 200
        else:
            return {'error': 'Invalid username or password'}, 401

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
    def get(self):
        quizzes = Quiz.query.all()
        quiz_list = []
        for quiz in quizzes:
            questions = [{'id': q.id, 'text': q.text, 'options': q.options.split(', ')} for q in quiz.questions]
            quiz_list.append({'id': quiz.id, 'title': quiz.title, 'questions': questions})
        return jsonify({'quizzes': quiz_list})

    def post(self):
        data = quiz_parser.parse_args()
        try:
            new_quiz = Quiz(title=data['title'])
            db.session.add(new_quiz)
            db.session.commit()
            return jsonify({'message': 'Quiz created', 'quiz': new_quiz.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating quiz: {str(e)}'}, 500

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
