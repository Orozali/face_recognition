from sqlalchemy import Column, ForeignKey, Integer, Time, func
from app.core.database import Base
from sqlalchemy.orm import relationship

class TemporaryAttendance(Base):
    __tablename__ = "temporary_attendance"
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("student.id"), nullable=False, index=True)
    entry_time = Column(Time, nullable=False, server_default=func.now())  
    timetable_id = Column(Integer, ForeignKey("timetable.id"), nullable=True, index=True)

    timetable = relationship("Timetable", back_populates="temporary_attendances")
    student = relationship("Student", back_populates="temporary_attendances") 