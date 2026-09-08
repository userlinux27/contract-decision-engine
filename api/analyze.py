"""
Analyze API v1.0
API для анализа контрактов.
"""

import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
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
    background_tasks: BackgroundTasks = None,
    # Template attribution fields (optional, from template page CTA)
    template_slug: str = Form(None),
    cta_location: str = Form(None),
    template_page_url: str = Form(None),
    template_referrer: str = Form(None),
    template_timestamp: str = Form(None),
    # Tool attribution fields (optional, from Free Tool page)
    tool_slug: str = Form(None),
    tool_page_url: str = Form(None),
    tool_referrer: str = Form(None),
    tool_utm_source: str = Form(None),
    tool_utm_medium: str = Form(None),
    tool_utm_campaign: str = Form(None),
    tool_timestamp: str = Form(None)
):
    """
    Загружает PDF контракт и запускает анализ.
    
    Args:
        file: PDF файл контракта
        background_tasks: FastAPI BackgroundTasks для асинхронной обработки
        template_slug: slug шаблона, с которого пришел пользователь
        cta_location: расположение CTA (hero_button, inline_banner, bottom_banner)
        template_page_url: URL страницы шаблона
        template_referrer: referrer страницы шаблона
        template_timestamp: timestamp посещения шаблона
        tool_slug: slug инструмента (contract-risk-checker)
        tool_page_url: URL страницы инструмента
        tool_referrer: referrer страницы инструмента
        tool_utm_source: UTM source
        tool_utm_medium: UTM medium
        tool_utm_campaign: UTM campaign
        tool_timestamp: timestamp посещения инструмента
        
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
    
    # 5. Логируем событие с атрибуцией шаблона и инструмента
    log_event(
        task_id, 
        "upload", 
        file_size_kb=len(contents) // 1024,
        template_slug=template_slug,
        cta_location=cta_location,
        template_page_url=template_page_url,
        template_referrer=template_referrer,
        template_timestamp=template_timestamp,
        tool_slug=tool_slug,
        tool_page_url=tool_page_url,
        tool_referrer=tool_referrer,
        tool_utm_source=tool_utm_source,
        tool_utm_medium=tool_utm_medium,
        tool_utm_campaign=tool_utm_campaign,
        tool_timestamp=tool_timestamp
    )
    
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


