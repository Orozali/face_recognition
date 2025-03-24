from insightface.app import FaceAnalysis
from app.minio.config import minio_client, bucket_name
from app.minio.config import get_all_embeddings_from_minio

from sklearn.metrics.pairwise import cosine_similarity

from app.models.student import Student
from app.models.timetable import Timetable
from app.models.lessons import Lesson
from app.models.temporary_db import TemporaryAttendance

from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import numpy as np
import logging
import cv2


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)

face_app = FaceAnalysis(
    name='buffalo_l',
    root='insightface_model',
    providers=['CUDAExecutionProvider']
)
face_app.prepare(ctx_id=0, det_size=(640,640), det_thresh=0.5)


async def process_frame(image_data: str, db: AsyncSession):
    nparr = np.frombuffer(image_data, np.uint8)
    logger.debug(f"Received image data size: {len(nparr)} bytes")
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    faces = face_app.get(frame)

    logger.debug(f"Students faces successfully received!: {len(faces)}")
    student_info = []
    
    stored_embeddings = get_all_embeddings_from_minio()
    logger.debug(f"Embeddings from minio successfully received: {len(stored_embeddings)}")

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
            await save_to_db(student, db)
        else:
            student_info.append({"id":"Unknown", "name": "Unknown", "surname": "Unknown", "student_id": "Unknown", "bbox": bbox})

    return {"students": student_info}


def ml_search_algorithm(stored_embeddings, test_vector, thresh=0.5):

    if not stored_embeddings:
        return 'Unknown'
    logger.debug("IT is not Unknown")
    student_ids = list(stored_embeddings.keys())
    logger.debug(f"Ids of students: {student_ids}")
    X_list = np.asarray(list(stored_embeddings.values()))
    similarity = cosine_similarity(X_list, test_vector.reshape(1, -1))
    similarity_arr = np.asarray(similarity).flatten()
    
    best_match_idx = np.argmax(similarity_arr)
    best_match_score = similarity[best_match_idx]
    logger.debug(f"Match score: {best_match_score}")
    
    if best_match_score >= thresh:
        return student_ids[best_match_idx]
    return 'Unknown'


async def get_student_details(student_id, db: AsyncSession, bbox) -> Student:
    result = await db.execute(
        select(Student.id, Student.name, Student.surname, Student.student_id)
        .where(Student.student_id == student_id)
    )
    student = result.fetchone()

    if student:
        return {"id": student.id, "name": student.name, "surname": student.surname, "student_id": student.student_id, "bbox": bbox}
 
    return None


async def save_to_db(student_info: dict, db: AsyncSession):
    """
    Save recognized student to the temporary attendance table if they are part of the active lesson.
    
    :param student_info: Dict containing recognized student's ID and bounding box.
    :param db: AsyncSession instance.
    """
    try:
        current_time = datetime.now().time()
        current_day = datetime.now().strftime("%A").upper()

        stmt = select(Timetable).where(
            Timetable.day == current_day,
            Timetable.start_time <= current_time,
            Timetable.end_time >= current_time
        ).options(selectinload(Timetable.lesson).selectinload(Lesson.students))
        timetable_result = await db.execute(stmt)
        active_timetable = timetable_result.scalars().first()


        if not active_timetable:
            logger.warning("No active lesson found at this time.")
            return

        lesson = active_timetable.lesson
        enrolled_students = {s.id for s in lesson.students}

        student_id = student_info.get("id")
        if student_id not in enrolled_students:
            return

        stmt = select(TemporaryAttendance).where(
            TemporaryAttendance.student_id == student_id,
            TemporaryAttendance.timetable_id == active_timetable.id
        )
        existing_entry = (await db.execute(stmt)).scalars().first()

        if existing_entry:
            logger.info(f"Student {student_id} is already recorded in temporary attendance. Skipping.")
            return 

        temp_attendance = TemporaryAttendance(
            student_id=student_id,
            timetable_id=active_timetable.id,
            entry_time=datetime.now().time()
        )
        db.add(temp_attendance)
        await db.commit()
        logger.info(f"Student {student_id} successfully added to temporary attendance.")

    except Exception as e:
        logger.error(f"Error saving to temporary attendance: {e}")
        await db.rollback()


