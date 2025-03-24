from sqlalchemy import Column, Integer, ForeignKey, Table
from app.core.database import Base

student_lesson_association = Table(
    "student_lesson",
    Base.metadata,
    Column("student_id", Integer, ForeignKey("student.id"), primary_key=True),
    Column("lesson_id", Integer, ForeignKey("lesson.id"), primary_key=True)
)
