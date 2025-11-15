# app/controllers/task_controller.py

from app.schemas.request.task_request import TaskRequest
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.response.task_response import TaskResponse
from db.client import client
from app.services import task_service as TaskService

router = APIRouter()

@router.get("/", response_model=list[TaskResponse])
async def list_tasks_route(db: Session = Depends(client)):
    return TaskService.find_all(db)

@router.get("/{task_id}" , response_model=TaskResponse)
async def show_task_route(task_id: str, db: Session = Depends(client)):
    return TaskService.find(db, task_id)

@router.post("/", status_code=201, response_model=TaskResponse)
async def create_task_route(data: TaskRequest, db: Session = Depends(client)):
    return TaskService.create(db, data)

@router.put("/{task_id}", response_model=TaskResponse)
async def edit_task_route(task_id: str, data: TaskRequest, db: Session = Depends(client)):
    return TaskService.update(db, task_id, data)

@router.delete("/{task_id}")
async def delete_task_route(task_id: str, db: Session = Depends(client)):
    return TaskService.destroy(db, task_id)

@router.get("/{task_id}/results")
async def get_task_results_route(task_id: str, db: Session = Depends(client)):
    return TaskService.results(db, task_id)
