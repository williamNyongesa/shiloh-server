from faker import Faker
from app import db 
from app.models import Student

fake = Faker()

def seed_student(n=10):
    """Seeds students into the database."""
    for _ in range(n):
        pass
  
        db.session.add(student)
    db.session.commit()