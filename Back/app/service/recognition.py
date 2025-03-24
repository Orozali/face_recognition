from app.websocket.manager import ws_manager
from datetime import datetime, timedelta
import asyncio
from app.core.database import async_session_maker
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_
from enum import Enum

from app.models.timetable import Timetable
from app.models.timetable_times import Timetable_times
from app.models.timetable import DaysEnum
from app.models.student import Student
from app.models.lessons import Lesson
from app.models.temporary_db import TemporaryAttendance
from app.models.user import User
from app.models.teacher import Teacher

async def capture_faces(lesson_time):
    start_time = datetime.strptime(lesson_time, "%H:%M")
    end_time = start_time + timedelta(minutes=45)
    today = datetime.now()

    async with async_session_maker() as session:
        result = await session.execute(
            select(Timetable)
            .join(Timetable_times, Timetable.id == Timetable_times.timetable_id)
            .options(
                selectinload(Timetable.lesson)
                .selectinload(Lesson.students)
            )
            .filter(
                Timetable.day == DaysEnum[today.strftime('%A').upper()],
                Timetable_times.start_time == start_time.time(),
                Timetable_times.end_time == end_time.time()
            )
        )

        timetables = result.scalars().all()

    return timetables


