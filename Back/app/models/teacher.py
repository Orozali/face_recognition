from sqlalchemy import Column, ForeignKey, Integer, String
from app.core.database import Base
from sqlalchemy.orm import relationship

class Teacher(Base):
    __tablename__ = "teacher"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, index=True)
    surname = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    image = Column(String, nullable=True)

    lessons = relationship("Lesson", back_populates="teacher", cascade="all, delete-orphan")
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    user = relationship("User", back_populates="teacher", uselist=False, cascade="all, delete", single_parent=True)  # uselist=False ensures one-to-one

    def __str__(self):
        return f"{self.name} {self.surname}"
