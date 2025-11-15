from sqlalchemy.orm import Session
from app.models.webhook import Webhook
from app.schemas.request.task_request import TaskRequest
from app.models.task import Task
from app.models.result import TaskResult
from lib.exception.not_found import NotFoundException

def find_all(db: Session):
    """List all tasks."""
    tasks = db.query(Task).all()
    return [task for task in tasks]

def find(db: Session, task_id: str):
    """Retrieve a task by ID."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundException
    
    return task

def create(db: Session, data: TaskRequest):
    """Create and schedule a new task."""
    task_data = data.model_dump()
    webhook_data = task_data.pop("webhook", None)

    if webhook_data:
        webhook = Webhook(**webhook_data)
        task_data["webhook"] = webhook

    task = Task(**task_data)
    db.add(task)
    db.commit()
    return task

def update(db: Session, task_id: str, data: TaskRequest):
    """Edit an existing task and update its schedule."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundException
    
    task_data = data.model_dump()
    webhook_data = task_data.pop("webhook", None)

    if webhook_data:
        webhook = task.webhook
        for key, value in webhook_data.items():
            setattr(webhook, key, value)
        task_data["webhook"] = webhook
        db.add(webhook)

    for key, value in task_data.items():
        setattr(task, key, value)
    db.add(task)

    db.commit()
    return task

def destroy(db: Session, task_id: str):
    """Delete a task and remove its schedule."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise NotFoundException

    db.delete(task)
    db.commit()
    return {"status": "success", "message": "Task deleted"}

def results(db: Session, task_id: str):
    """Retrieve all execution results for a given task."""
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise NotFoundException
    
    results = db.query(TaskResult).filter(TaskResult.task_id == task_id).all()
    return [result.to_dict() for result in results]
