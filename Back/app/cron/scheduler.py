import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from datetime import datetime, timedelta
from app.websocket.manager import ws_manager

scheduler = BackgroundScheduler()

# LESSON_TIMES = ["08:00", "08:55", "09:50", "10:45", "11:40", "13:30", "14:25", "15:20", "16:15", "17:10", "18:05"]
LESSON_TIMES = ["08:00", "08:55", "09:50", "10:45", "11:15", "13:30", "14:25", "15:20", "16:15", "17:10", "18:05"]


# async def run_capture_faces(lesson_time: str):
#     await capture_faces(lesson_time)
def set_websocket(lesson_time: str):
    ws_manager.set_cron_active(True)
    ws_manager.set_lesson_time(lesson_time)

def set_cron_disactive():
    ws_manager.set_cron_active(False)


def start_schedulers():
    for lesson_time in LESSON_TIMES:
        if lesson_time:
            if lesson_time == LESSON_TIMES[-1]:
                lesson_time_ = datetime.strptime(lesson_time, "%H:%M")
                trigger_time = lesson_time_ + timedelta(minutes=45)
                trigger_hour = trigger_time.hour
                trigger_minute = trigger_time.minute

                scheduler.add_job(
                    set_cron_disactive,
                    CronTrigger(hour=trigger_hour, minute=trigger_minute, day_of_week="0-4"),
                )
            try:
                print(f"Processing lesson time: {lesson_time}")
                
                start_hour, start_minute = map(int, lesson_time.split(":"))

                if start_minute < 10:
                    adjusted_hour = start_hour - 1
                    adjusted_minute = (start_minute - 10) % 60
                else:
                    adjusted_hour = start_hour
                    adjusted_minute = start_minute - 10

                scheduler.add_job(
                    # lambda: asyncio.run(run_capture_faces(lesson_time)),
                    set_websocket,
                    CronTrigger(hour=adjusted_hour, minute=adjusted_minute, day_of_week="0-4"),
                    args=[lesson_time],
                    id=f"capture_{lesson_time.replace(':', '')}"
                )
            except ValueError as e:
                print(f"Invalid lesson time format: {lesson_time} -> Error: {e}")

    scheduler.start()
    print("All cron jobs started (Monday to Friday)")

if not scheduler.running:
    start_schedulers()
