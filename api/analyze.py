"""
Analyze API v1.0
API для анализа контрактов.
"""

import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from services.task_service import task_service, TaskStatus
from services.document_service import DocumentService
from services.analysis_service import AnalysisService
from utils.logging import log_event

# Создаём роутер
router = APIRouter(prefix="/api", tags=["analysis"])

# Создаём сервисы
document_service = DocumentService()
analysis_service = AnalysisService(task_service)


@router.post("/analyze")
async def analyze_contract(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Загружает PDF контракт и запускает анализ.
    
    Args:
        file: PDF файл контракта
        background_tasks: FastAPI BackgroundTasks для асинхронной обработки
        
    Returns:
        JSONResponse с task_id и статусом
    """
    # 1. Читаем содержимое файла
    contents = await file.read()
    
    # 2. Валидация файла
    is_valid, error_message = document_service.validate_pdf(file.filename, contents)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=error_message
        )
    
    # 3. Создаём задачу
    task_id = task_service.create_task()
    
    # 4. Сохраняем файл
    filepath = document_service.save_document(task_id, contents)
    
    # 5. Логируем событие
    log_event(task_id, "upload", file_size_kb=len(contents) // 1024)
    
    # 6. Запускаем анализ в фоне
    if background_tasks:
        background_tasks.add_task(
            analysis_service.analyze_contract,
            task_id=task_id,
            filepath=filepath
        )
    else:
        # Если нет background_tasks, запускаем асинхронно
        import asyncio
        asyncio.create_task(
            analysis_service.analyze_contract(task_id=task_id, filepath=filepath)
        )
    
    # 7. Возвращаем ответ
    return JSONResponse({
        "task_id": task_id,
        "status": TaskStatus.PROCESSING,
        "message": "Analyzing your contract..."
    }, status_code=202)  # 202 Accepted для асинхронной задачи


@router.get("/health")
async def health_check():
    """
    Проверка здоровья API.
    
    Returns:
        JSONResponse с статусом сервиса
    """
    return JSONResponse({
        "status": "healthy",
        "service": "Contract Decision Engine API",
        "version": "v1.0"
    })
