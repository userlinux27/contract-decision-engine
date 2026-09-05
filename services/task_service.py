"""
Task Service v1.0
Управление задачами анализа контрактов.

Отвечает за:
- Создание task_id
- Хранение статуса задачи
- Обновление результата/ошибки
- Проверка статуса задачи
"""

import uuid
from typing import Dict, Optional, Any
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Статусы задачи."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskService:
    """Сервис управления задачами."""
    
    def __init__(self):
        self._tasks: Dict[str, Dict] = {}
    
    def create_task(self) -> str:
        """
        Создаёт новую задачу.
        
        Returns:
            str: task_id новой задачи
        """
        task_id = str(uuid.uuid4())
        
        self._tasks[task_id] = {
            "task_id": task_id,
            "status": TaskStatus.PROCESSING,
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None,
            "progress": 0,
            "message": "Starting analysis..."
        }
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """
        Получает информацию о задаче.
        
        Args:
            task_id: идентификатор задачи
            
        Returns:
            Dict: информация о задаче или None если задача не найдена
        """
        return self._tasks.get(task_id)
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None
    ) -> bool:
        """
        Обновляет статус задачи.
        
        Args:
            task_id: идентификатор задачи
            status: новый статус
            result: результат анализа (если есть)
            error: сообщение об ошибке (если есть)
            progress: прогресс выполнения (0-100)
            message: сообщение о текущем статусе
            
        Returns:
            bool: True если задача обновлена, False если задача не найдена
        """
        if task_id not in self._tasks:
            return False
        
        task = self._tasks[task_id]
        task["status"] = status
        task["updated_at"] = datetime.utcnow().isoformat()
        
        if result is not None:
            task["result"] = result
        
        if error is not None:
            task["error"] = error
        
        if progress is not None:
            task["progress"] = progress
        
        if message is not None:
            task["message"] = message
        
        return True
    
    def complete_task(self, task_id: str, result: Dict) -> bool:
        """
        Помечает задачу как завершённую.
        
        Args:
            task_id: идентификатор задачи
            result: результат анализа
            
        Returns:
            bool: True если задача обновлена, False если задача не найдена
        """
        return self.update_task_status(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            result=result,
            progress=100,
            message="Analysis completed"
        )
    
    def fail_task(self, task_id: str, error: str) -> bool:
        """
        Помечает задачу как неудачную.
        
        Args:
            task_id: идентификатор задачи
            error: сообщение об ошибке
            
        Returns:
            bool: True если задача обновлена, False если задача не найдена
        """
        return self.update_task_status(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error=error,
            progress=0,
            message=f"Analysis failed: {error}"
        )
    
    def update_progress(self, task_id: str, progress: int, message: str) -> bool:
        """
        Обновляет прогресс выполнения задачи.
        
        Args:
            task_id: идентификатор задачи
            progress: прогресс выполнения (0-100)
            message: сообщение о текущем статусе
            
        Returns:
            bool: True если задача обновлена, False если задача не найдена
        """
        return self.update_task_status(
            task_id=task_id,
            status=TaskStatus.PROCESSING,
            progress=progress,
            message=message
        )
    
    def cleanup_old_tasks(self, hours: int = 24):
        """
        Удаляет старые задачи.
        
        Args:
            hours: задачи старше этого количества часов будут удалены
        """
        now = datetime.utcnow()
        
        tasks_to_remove = []
        for task_id, task in self._tasks.items():
            created_at = datetime.fromisoformat(task["created_at"])
            age_hours = (now - created_at).total_seconds() / 3600
            
            if age_hours > hours:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self._tasks[task_id]


# Глобальный экземпляр сервиса задач
task_service = TaskService()
