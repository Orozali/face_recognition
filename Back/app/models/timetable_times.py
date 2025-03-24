from sqlalchemy import Column, ForeignKey, Integer, Time
from app.core.database import Base
from sqlalchemy.orm import relationship


class Timetable_times(Base):
    __tablename__ = "timetable_times"
    id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    timetable_id = Column(Integer, ForeignKey("timetable.id"), nullable=True)

    timetable = relationship("Timetable", back_populates="timetable_times")
    def __str__(self):
        return self.start_time +" | "+self.end_time