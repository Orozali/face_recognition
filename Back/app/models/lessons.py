from sqlalchemy import Column, ForeignKey, Integer, String
from app.core.database import Base
from sqlalchemy.orm import relationship
from app.models.student_lesson import student_lesson_association

class Lesson(Base):
    __tablename__ = "lesson"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, index=True)
    code = Column(String, index=True)

    teacher_id = Column(Integer, ForeignKey("teacher.id"), nullable=True)
    teacher = relationship("Teacher", back_populates="lessons")
    students = relationship("Student", secondary=student_lesson_association, back_populates="lessons")
    timetables = relationship("Timetable", back_populates="lesson", cascade="all, delete-orphan")

    def __str__(self):
        return self.code+': '+self.name