from app.celery import scheduler
from celery.schedules import crontab
from datetime import datetime, timedelta, timezone

from typing import Optional

def enqueue(task: callable, kwargs: dict, scheduled_time: Optional[str] = None, cron: Optional[str] = None):
    """Add a scheduled task to Celery Beat."""
    task_id = kwargs["task_id"]
    scheduled_time = scheduled_time if scheduled_time != None else (datetime.now() + timedelta(minutes=5)).isoformat()
    if cron != None:
        scheduler.add_periodic_task(
            crontab(cron), 
            task.s(**kwargs), 
            f"cron_{task.__name__}_{task_id}"
        )
    else:
        scheduler.add_periodic_task(
            datetime.fromisoformat(scheduled_time).replace(tzinfo=timezone.utc),
            task.s(**kwargs), 
            f"{task.__name__}_{task_id}"
        )
