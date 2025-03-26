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


async def process_frame(faces: list, all_embddings: list, db: AsyncSession):
    logger.debug(f"Students faces successfully received!: {len(faces)}")
    student_info = []
    
    for face in faces:
        bbox = face.bbox.astype(int).tolist()
        embedding = face.embedding
        logger.debug("Embedding is received")
        
        matched_student = ml_search_algorithm(all_embddings, embedding, thresh=0.5)
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


async def save_to_db(student_info: dict, timetable_id: int, session: AsyncSession):
    """
    Save recognized student to the temporary attendance table if they are part of the active lesson
    and have not been recorded already.

    :param student_info: Dict containing recognized student's ID and bounding box.
    :param timetable_id: The ID of the timetable entry.
    :param session: AsyncSession instance.
    """
    try:
        current_time = datetime.now().time()
        student_id = student_info.get("id")

        student = await session.execute(
            select(Student).filter(Student.id == student_id)
        )
        student = student.scalars().first()

        if student:
            # ✅ Check if student is already recorded in temporary attendance
            existing_record = await session.execute(
                select(TemporaryAttendance).filter(
                    TemporaryAttendance.student_id == student_id,
                    TemporaryAttendance.timetable_id == timetable_id
                )
            )
            existing_record = existing_record.scalars().first()

            if existing_record:
                logger.debug(f"Student {student.name} {student.surname} is already recorded in temporary attendance.")
            else:
                temp_attendance = TemporaryAttendance(
                    student_id=student.id,
                    timetable_id=timetable_id,
                    entry_time=current_time
                )
                
                session.add(temp_attendance)
                await session.commit()
                logger.debug(f"Student {student.name} {student.surname} added to temporary attendance.")
        
        else:
            logger.debug(f"Student with ID {student_id} not found.")
        
    except Exception as e:
        logger.error(f"Error saving to temporary attendance: {e}")
        await session.rollback()



def is_student_in_timetable(matched_student, timetables: list):
    """
    Checks if the matched student is in any timetable's lesson students list.

    Args:
    - matched_student (Student): The student object containing an ID.
    - timetables (list[Timetable]): List of timetable objects.

    Returns:
    - tuple: (bool, timetable_id) → True if student exists, along with timetable_id.
    """
    for timetable in timetables:
        if any(student.id == matched_student.id for student in timetable.lesson.students):
            return True, timetable.id  # Found the student, return immediately

    return False, None


async def get_student_details(student_id, db: AsyncSession, bbox) -> Student:
    result = await db.execute(
        select(Student.id, Student.name, Student.surname, Student.student_id)
        .where(Student.student_id == student_id)
    )
    student = result.fetchone()

    if student:
        return {"id": student.id, "name": student.name, "surname": student.surname, "student_id": student.student_id, "bbox": bbox}
 
    return None
