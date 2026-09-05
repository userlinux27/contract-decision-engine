"""
Pydantic Schemas v0.2
Схемы данных для API и Decision Engine.

Используются для валидации входящих данных от LLM и ответов API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class DocumentType(str, Enum):
    """Типы документов."""
    SERVICE_AGREEMENT = "service_agreement"
    NDA = "nda"
    EMPLOYMENT_CONTRACT = "employment_contract"
    TENANCY_AGREEMENT = "tenancy_agreement"
    UNKNOWN = "unknown"


class ParsedDocument(BaseModel):
    """Схема: результат парсинга PDF документа."""
    
    text: str = Field(..., description="Полный текст документа")
    pages: int = Field(..., description="Количество страниц")
    language: str = Field(default="en", description="Язык документа")
    estimated_reading_time_min: int = Field(..., description="Примерное время чтения в минутах")
    metadata: Dict = Field(default_factory=dict, description="Метаданные документа")


class ClassificationResult(BaseModel):
    """Схема: результат классификации документа."""
    
    document_type: DocumentType = Field(..., description="Тип документа")
    display_name: str = Field(..., description="Отображаемое имя документа")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность классификации")
    supported: bool = Field(..., description="Поддерживается ли полный анализ")
    key_clauses_found: List[str] = Field(default_factory=list, description="Найденные ключевые пункты")


class FindingInput(BaseModel):
    """Входная схема: один найденный фактор от LLM."""

    type: str = Field(..., description="Тип фактора из Decision Catalogue")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность LLM")
    reason: str = Field(..., description="Объяснение на человеческом языке")
    original_text: str = Field(..., description="Исходный текст из договора")
    suggested_rewrite: Optional[str] = Field(
        None, description="Безопасная формулировка или null"
    )


class ClauseAnalysis(BaseModel):
    """Входная схема: анализ одного пункта договора."""

    clause: str = Field(..., description="Номер пункта (например, '4.2')")
    findings: list[FindingInput] = Field(
        default_factory=list, description="Список найденных факторов"
    )


class DecisionOutput(BaseModel):
    """Выходная схема: результат Decision Engine."""

    decision: str = Field(
        ..., description="safe_to_sign | sign_after_changes | do_not_sign"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Агрегированная уверенность")
    top_reasons: list[dict] = Field(
        ..., description="Топ-3 причины с factor, weight, reason"
    )
    all_findings: list[dict] = Field(..., description="Все найденные факторы")
    total_weight: int = Field(..., description="Суммарный вес")


class AnalysisResult(BaseModel):
    """Схема: итоговый результат анализа для frontend."""
    
    classification: ClassificationResult = Field(..., description="Результат классификации")
    pipeline: Dict = Field(..., description="Информация о pipeline обработки")
    decision: str = Field(..., description="Итоговое решение")
    decision_details: DecisionOutput = Field(..., description="Детали решения")
    decision_labels: Dict[str, str] = Field(..., description="Лейблы решений")


class FeedbackInput(BaseModel):
    """Входная схема: обратная связь от пользователя."""

    visitor_id: str = Field(..., description="ID посетителя")
    action: Optional[str] = Field(
        None, description="signed | changes | walked | deciding"
    )
    useful: Optional[str] = Field(None, description="yes | no")
    time_to_decision: Optional[int] = Field(
        None, description="Секунды до ответа"
    )


class CopyEventInput(BaseModel):
    """Входная схема: событие копирования suggested wording."""

    visitor_id: str = Field(..., description="ID посетителя")
    clause: str = Field(..., description="Номер пункта")
