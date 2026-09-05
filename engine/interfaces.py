"""
Pipeline Interfaces v0.1
Интерфейсы для модулей pipeline анализа документов.

Определяют контракты между компонентами системы.
"""

from abc import ABC, abstractmethod
from typing import Optional
from engine.schemas import ParsedDocument, ClassificationResult, FindingInput


class PDFParserInterface(ABC):
    """Интерфейс парсера PDF документов."""
    
    @abstractmethod
    def parse(self, filepath: str) -> ParsedDocument:
        """
        Извлекает текст и метаданные из PDF.
        
        Args:
            filepath: путь к PDF файлу
            
        Returns:
            ParsedDocument: результат парсинга
        """
        pass


class ClassifierInterface(ABC):
    """Интерфейс классификатора документов."""
    
    @abstractmethod
    def classify(self, document: ParsedDocument) -> ClassificationResult:
        """
        Классифицирует тип документа.
        
        Args:
            document: распарсенный документ
            
        Returns:
            ClassificationResult: результат классификации
        """
        pass


class RuleDetectorInterface(ABC):
    """Интерфейс детектора правил/факторов."""
    
    @abstractmethod
    def detect(self, document: ParsedDocument) -> list[FindingInput]:
        """
        Обнаруживает факторы риска в документе.
        
        Args:
            document: распарсенный документ
            
        Returns:
            list[FindingInput]: найденные факторы риска
        """
        pass


class LLMServiceInterface(ABC):
    """Интерфейс сервиса LLM."""
    
    @abstractmethod
    def enrich_findings(self, findings: list[FindingInput]) -> list[dict]:
        """
        Обогащает найденные факторы через LLM.
        
        Args:
            findings: список найденных факторов
            
        Returns:
            list[dict]: обогащённые факторы с LLM объяснениями
        """
        pass
