from datetime import datetime
from flask_restx import Namespace, Resource, reqparse
from app import db
from app.models import Student

students_ns = Namespace('students', description='Student management operations')

student_parser = reqparse.RequestParser()
student_parser.add_argument('name', type=str, required=True, help='Name of the student')
student_parser.add_argument('email', type=str, required=True, help='Email of the student')
student_parser.add_argument('phone_number', type=str, required=True, help='Phone number of the student')

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
        student_count = Student.query.count() + 1  # Get the count for student_id generation
        campus_code = "KE"  # Replace with the actual logic to get the campus code
        student_id = Student.generate_student_id(campus_code, student_count)

        new_student = Student(
            name=data['name'],
            email=data['email'],
            phone_number=data['phone_number'],
            student_id=student_id,  # Use generated student_id
            enrolled_date=datetime.now() 
        )
        db.session.add(new_student)
        db.session.commit()
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
