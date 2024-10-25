# app/models.py
from app import db
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime

class Student(db.Model, SerializerMixin):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)  
    enrolled_date = db.Column(db.DateTime, default=datetime.now())  # Use utcnow for consistent timestamps

    def __repr__(self):
        return f'<Student {self.name}, {self.student_id}>'
    
    @staticmethod
    def generate_student_id(campus_code, student_count):
        """Generates a student ID like KE-0001."""
        return f"{campus_code}-{str(student_count).zfill(4)}"
