from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.service.recognition import capture_faces

scheduler = BackgroundScheduler()

LESSON_TIMES = ["08:00", "08:55", "09:50", "10:45", "11:40", "12:35", "13:30", "14:06", "15:20", "16:15"]

def start_schedulers():
    for lesson_time in LESSON_TIMES:
        if lesson_time:
            try:
                start_hour, start_minute = map(int, lesson_time.split(":"))
                
                if start_minute < 10:
                    adjusted_hour = start_hour - 1
                    adjusted_minute = (start_minute - 10) % 60
                else:
                    adjusted_hour = start_hour
                    adjusted_minute = start_minute - 10

                scheduler.add_job(
                    capture_faces,
                    CronTrigger(hour=adjusted_hour, minute=adjusted_minute, day_of_week="0-4"),
                    args=[lesson_time],
                    id=f"capture_{lesson_time.replace(':', '')}"
                )
            except ValueError:
                print(f"Invalid lesson time format: {lesson_time}")

    scheduler.start()
    print("All cron jobs started (Monday to Friday)")

if not scheduler.running:
    start_schedulers()
