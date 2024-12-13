from flask_jwt_extended import create_access_token
from flask_bcrypt import Bcrypt
from flask_restx import Namespace, Resource, reqparse
from datetime import datetime
from app import db
from app.models import Student, User, Teacher, Finance, Enrollment, Event

from werkzeug.utils import secure_filename
import os
from io import BytesIO
from flask import request, jsonify
from app import db
from app.models import Quiz, Question  # Assuming Quiz and Question models exist
# Initialize Bcrypt
bcrypt = Bcrypt()

# Namespaces
students_ns = Namespace('students', description='Student management operations')
users_ns = Namespace('users', description='User management operations')
teachers_ns = Namespace('teachers', description='Teacher management operations')
finances_ns = Namespace('finances', description='Finance management operations')
enrollments_ns = Namespace('enrollments', description='Enrollment management operations')
quizzes_ns = Namespace('quizzes', description='Quiz management operations')
events_ns = Namespace('events', description='Event related operations')

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
# Quiz Parser (if needed)
quiz_parser = reqparse.RequestParser()
quiz_parser.add_argument('title', type=str, required=True, help='Title of the quiz')

# Question Parser (if needed)
question_parser = reqparse.RequestParser()
question_parser.add_argument('text', type=str, required=True, help='Text of the question')
question_parser.add_argument('options', type=str, required=True, help='Comma-separated options for the question')
question_parser.add_argument('correct_answer', type=str, required=True, help='Correct answer for the question')

# Student Routes
@students_ns.route('')
class StudentListResource(Resource):
    def get(self):
        """Fetch all users"""
        users = User.query.all()
        return [user.to_dict() for user in users], 200

    def post(self):
        """Create a new user"""
        data = user_parser.parse_args()

        existing_user_by_email = User.query.filter_by(email=data['email']).first()
        existing_user_by_username = User.query.filter_by(username=data['username']).first()

        if existing_user_by_email:
            return {'message': 'User with this email already exists.'}, 400  # Bad request
        
        if existing_user_by_username:
            return {'message': 'User with this username already exists.'}, 400  # Bad request

        try:
            # Create a new user
            new_user = User(
                username=data['username'],
                email=data['email'],
                password=data['password']  # Ensure to hash the password before saving in a real app
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            return new_user.to_dict(), 201 

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating user: {str(e)}'}, 500

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
        """Create a new enrollment with document upload"""
        data = enrollment_parser.parse_args()

        # Retrieve the student
        student = Student.query.get(data['student_id'])
        if not student:
            return {'message': 'Student not found'}, 404

        if not data['courses'] or not data['phone_number']:
            return {"message": "Missing required fields: courses or phone_number"}, 400
        
        # Retrieve document file from the request
        document = request.files.get('document_file')  # Assuming the file is sent with the key 'document_file'

        if document:
            try:
                # Ensure that the file is a valid document (you can add checks for file type here)
                filename = secure_filename(document.filename)
                file_data = document.read()  # Get the binary data of the file
                
                # Create the new enrollment with document file
                new_enrollment = Enrollment(
                    student_id=data['student_id'],
                    courses=data['courses'],
                    phone_number=data['phone_number'],
                    enrollment_date=data.get('enrollment_date', datetime.now()),
                    document_file=file_data  # Store the binary document data here
                )
                
                db.session.add(new_enrollment)
                db.session.commit()
                return new_enrollment.to_dict(), 201
            
            except Exception as e:
                db.session.rollback()  # Rollback in case of error
                return {"message": f"Error saving enrollment with document: {str(e)}"}, 500
        else:
            return {"message": "Missing document file"}, 400


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

# Endpoint to fetch quizzes with questions
@quizzes_ns.route('')
class QuizListResource(Resource):
    def get(self):
        """Fetch all quizzes with their questions"""
        quizzes = Quiz.query.all()
        quiz_list = []
        for quiz in quizzes:
            questions = [{'id': q.id, 'text': q.text, 'options': q.options.split(', ')} for q in quiz.questions]
            quiz_list.append({'id': quiz.id, 'title': quiz.title, 'questions': questions})
        return jsonify({'quizzes': quiz_list})

    def post(self):
        """Create a new quiz"""
        data = quiz_parser.parse_args()
        try:
            new_quiz = Quiz(title=data['title'])
            db.session.add(new_quiz)
            db.session.commit()
            return jsonify({'message': 'Quiz created', 'quiz': new_quiz.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating quiz: {str(e)}'}, 500


# Endpoint to manage quiz questions
@quizzes_ns.route('/<int:quiz_id>/questions')
class QuizQuestionListResource(Resource):
    def get(self, quiz_id):
        """Fetch all questions for a specific quiz"""
        quiz = Quiz.query.get_or_404(quiz_id)
        questions = [{'id': q.id, 'text': q.text, 'options': q.options.split(', ')} for q in quiz.questions]
        return jsonify({'quiz_id': quiz.id, 'questions': questions})

    def post(self, quiz_id):
        """Add a question to a quiz"""
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


# Endpoint to submit answers for a quiz
@quizzes_ns.route('/submit-quiz', methods=['POST'])
class SubmitQuizResource(Resource):
    def post(self):
        """Submit answers for a quiz and calculate score"""
        try:
            data = request.get_json()
            quiz_id = data.get("quizId")
            answers = data.get("answers", {})

            # Fetch the quiz by ID
            quiz = Quiz.query.get(quiz_id)

            if not quiz:
                return {"error": "Quiz not found"}, 404

            # Calculate the score
            score = 0
            total_questions = len(quiz.questions)

            for question in quiz.questions:
                question_id = str(question.id)  # Convert to string to match the answers' keys
                correct_answer = question.correct_answer
                # Compare submitted answers with correct answers
                if answers.get(question_id) == correct_answer:
                    score += 1

            return {"score": score, "total": total_questions}, 200
        except Exception as e:
            return {"error": str(e)}, 500
        

@events_ns.route('')
class EventListResource(Resource):
    def get(self):
        """Retrieve all events"""
        events = Event.query.all()  # Retrieve all events from the database
        return [event.to_dict() for event in events], 200

    def post(self):
        """Create a new event or update an existing one"""
        try:
            data = request.get_json()

            title = data.get("title")
            date = data.get("date")
            description = data.get("description")
            time = data.get("time")
            location = data.get("location")

            # Validate required fields
            if not title or not date:
                return {"error": "Title and date are required fields."}, 400

            # Check if the event already exists by title and date
            event = Event.query.filter_by(title=title, date=date).first()

            if event:
                # Update the existing event
                event.description = description
                event.time = time
                event.location = location
                db.session.commit()
                return {"message": "Event updated successfully", "event": event.to_dict()}, 200
            else:
                # Create a new event
                new_event = Event(
                    title=title,
                    date=date,
                    description=description,
                    time=time,
                    location=location
                )
                db.session.add(new_event)
                db.session.commit()
                return {"message": "Event created successfully", "event": new_event.to_dict()}, 201

        except Exception as e:
            return {"error": str(e)}, 500

@events_ns.route('/submit-event', methods=['POST'])
class SubmitEventResource(Resource):
    def post(self):
        """Submit event data to create or update the event"""
        try:
            data = request.get_json()

            title = data.get("title")
            date = data.get("date")
            description = data.get("description")
            time = data.get("time")
            location = data.get("location")

            if not title or not date:
                return {"error": "Title and date are required fields."}, 400

            # Check if the event already exists by title and date
            event = Event.query.filter_by(title=title, date=date).first()

            if event:
                # Update the existing event
                event.description = description
                event.time = time
                event.location = location
                db.session.commit()
                return {"message": "Event updated successfully", "event": event.to_dict()}, 200
            else:
                # Create a new event
                new_event = Event(
                    title=title,
                    date=date,
                    description=description,
                    time=time,
                    location=location
                )
                db.session.add(new_event)
                db.session.commit()
                return {"message": "Event created successfully", "event": new_event.to_dict()}, 201

        except Exception as e:
            return {"error": str(e)}, 500
