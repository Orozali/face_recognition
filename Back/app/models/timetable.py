from sqlalchemy import Column, Integer, ForeignKey, Time, Enum, String
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class DaysEnum(enum.Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"

class Timetable(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lesson.id"), nullable=False)
    day = Column(Enum(DaysEnum), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    cabinet_num = Column(String, nullable=True)
    lesson = relationship("Lesson", back_populates="timetables")

    temporary_attendances = relationship("TemporaryAttendance", back_populates="timetable")
    timetable_times = relationship("Timetable_times", back_populates="timetable", cascade="all, delete")
    def __str__(self):
            return f"{self.id}"