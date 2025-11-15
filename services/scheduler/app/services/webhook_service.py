import requests
import json
from sqlalchemy.orm import Session
from app.models.task import Task
from app.models.result import TaskResult
from datetime import datetime

def trigger_webhook(db: Session, task_id: int):
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        return

    webhook = task.webhook
    headers = json.loads(webhook.headers) if webhook.headers else {}
    body = json.loads(webhook.body) if webhook.body else {}
    response = requests.request(webhook.method.value, webhook.url, json=body, headers=headers)
    save_result(db, task_id, response)

def save_result(db: Session, task_id: int, response=None, error=None):
    """Save the result of task execution to the database."""
    if response != None:
        response_body = None
        content_type = response.headers.get('content-type') or response.headers.get('Content-Type')
        if content_type.startswith('application/json'):
            response_body = response.json()
        else:
            response_body = response.text
    
        task_result = TaskResult(
            task_id=task_id,
            status="success" if response.status_code < 400 else "error",
            response_status=response.status_code if response != None else None,
            response_body=response_body,
            response_headers=json.dumps(dict(response.headers)) if response != None else None,
            error=error,
            timestamp=datetime.utcnow(),
        )
        db.add(task_result)
        db.commit()