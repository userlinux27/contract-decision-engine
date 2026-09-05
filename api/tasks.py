"""
Tasks API v1.0
API для управления задачами анализа.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.task_service import task_service, TaskStatus

# Создаём роутер
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """
    Получает статус задачи анализа.
    
    Args:
        task_id: идентификатор задачи
        
    Returns:
        JSONResponse с статусом и результатом (если есть)
    """
    task = task_service.get_task(task_id)
    
    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )
    
    # Формируем ответ в зависимости от статуса
    response = {
        "task_id": task_id,
        "status": task["status"],
        "created_at": task["created_at"]
    }
    
    if task.get("updated_at"):
        response["updated_at"] = task["updated_at"]
    
    if task.get("progress") is not None:
        response["progress"] = task["progress"]
    
    if task.get("message"):
        response["message"] = task["message"]
    
    if task["status"] == TaskStatus.COMPLETED and task.get("result"):
        response["result"] = task["result"]
    
    if task["status"] == TaskStatus.FAILED and task.get("error"):
        response["error"] = task["error"]
    
    return JSONResponse(response)


@router.get("/")
async def list_tasks(limit: int = 10):
    """
    Список последних задач.
    
    Args:
        limit: максимальное количество задач
        
    Returns:
        JSONResponse со списком задач
    """
    # Получаем все задачи и сортируем по времени создания
    all_tasks = list(task_service._tasks.values())
    sorted_tasks = sorted(
        all_tasks,
        key=lambda x: x["created_at"],
        reverse=True
    )[:limit]
    
    # Формируем упрощённый список
    tasks_list = []
    for task in sorted_tasks:
        tasks_list.append({
            "task_id": task["task_id"],
            "status": task["status"],
            "created_at": task["created_at"],
            "progress": task.get("progress", 0)
        })
    
    return JSONResponse({
        "tasks": tasks_list,
        "total": len(all_tasks)
    })
