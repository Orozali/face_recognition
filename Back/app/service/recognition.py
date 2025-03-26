from typing import Optional
from fastapi import WebSocket
from datetime import datetime, timedelta
from app.core.database import async_session_maker
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from insightface.app import FaceAnalysis
from sqlalchemy.ext.asyncio import AsyncSession

from app.minio.config import get_all_embeddings_from_minio
from app.service.insightface import is_student_in_timetable
from app.service.insightface import ml_search_algorithm
from app.service.insightface import save_to_db
from app.service.insightface import get_student_details
from app.service.insightface import process_frame
from app.websocket.manager import ws_manager

from app.models.timetable import Timetable
from app.models.timetable_times import Timetable_times
from app.models.timetable import DaysEnum
from app.models.student import Student
from app.models.lessons import Lesson
from app.models.temporary_db import TemporaryAttendance
from app.models.user import User
from app.models.teacher import Teacher

import numpy as np
import cv2

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

face_app = FaceAnalysis(
    name='buffalo_l',
    root='insightface_model',
    providers=['CUDAExecutionProvider']
)
face_app.prepare(ctx_id=0, det_size=(640,640), det_thresh=0.5)

latest_frame: Optional[np.ndarray] = None

async def capture_faces(image_data: str, db: AsyncSession):
    nparr = np.frombuffer(image_data, np.uint8)
    logger.debug(f"Received image data size: {len(nparr)} bytes")
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    faces = face_app.get(frame)

    logger.debug(f"Students faces successfully received!: {len(faces)}")
    student_info = []
    
    stored_embeddings = get_all_embeddings_from_minio()
    logger.debug(f"Embeddings from minio successfully received: {len(stored_embeddings)}")

    logger.debug(f"Students faces successfully received!: {len(faces)}")
    student_info = []
    
    for face in faces:
        bbox = face.bbox.astype(int).tolist()
        embedding = face.embedding
        logger.debug("Embedding is received")
        
        matched_student = ml_search_algorithm(stored_embeddings, embedding, thresh=0.5)
        logger.debug("Ml search algorithm worked")
        if matched_student != "Unknown":
            student = await get_student_details(matched_student, db, bbox)
            if not student:
                return {"error": "Student not found!"}
            student_info.append(student)
            logger.debug(f"Check cron active: {ws_manager.cron_active}")
            if ws_manager.cron_active:
                lesson_time = ws_manager.lesson_time
                logger.debug(f"Lesson time: {lesson_time}")
                if lesson_time is None:
                    logger.debug("Lesson time is none")
                    return 

                timetables = await get_timetables(lesson_time, db)
                is_student_exists, timetable_id = is_student_in_timetable(student, timetables)
                if is_student_exists:
                    await save_to_db(student, timetable_id, db)
        else:
            student_info.append({"id":"Unknown", "name": "Unknown", "surname": "Unknown", "student_id": "Unknown", "bbox": bbox})

    return {"students": student_info}


async def get_timetables(lesson_time: str, db: AsyncSession):
    start_time = datetime.strptime(lesson_time, "%H:%M")
    end_time = start_time + timedelta(minutes=45)
    today = datetime.now()

    result = await db.execute(
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





