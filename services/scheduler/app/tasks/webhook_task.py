from app.services.webhook_service import trigger_webhook
from db.client import SessionLocal
from celery import shared_task


@shared_task(rate_limit="10/m")
def webhook(task_id: int):
    db = SessionLocal()
    try:
        trigger_webhook(db, task_id)
    except Exception as e:
        print("Webhook Task Error:", e)
    finally:
        db.close()
