"""
Document Classifier v1.0
Классификация типов документов.

Реализация ClassifierInterface.
"""

import re
from typing import List
from engine.schemas import ParsedDocument, ClassificationResult, DocumentType
from engine.interfaces import ClassifierInterface
from engine.catalog import DOCUMENT_TYPES


class DocumentClassifier(ClassifierInterface):
    """
    Классификатор документов на основе ключевых слов.
    """
    
    def __init__(self):
        pass
    
    def classify(self, document: ParsedDocument) -> ClassificationResult:
        """
        Классифицирует тип документа.
        
        Args:
            document: распарсенный документ
            
        Returns:
            ClassificationResult: результат классификации
        """
        text_lower = document.text.lower()
        
        # Определяем тип документа по ключевым словам
        doc_type, confidence = self._determine_document_type(text_lower)
        
        # Находим ключевые пункты
        key_clauses = self._find_key_clauses(text_lower)
        
        # Получаем конфигурацию для этого типа документа
        type_config = DOCUMENT_TYPES.get(doc_type.value, DOCUMENT_TYPES["unknown"])
        
        return ClassificationResult(
            document_type=doc_type,
            display_name=type_config["display_name"],
            confidence=confidence,
            supported=type_config["supported"],
            key_clauses_found=key_clauses
        )
    
    def _determine_document_type(self, text: str) -> tuple[DocumentType, float]:
        """
        Определяет тип документа по ключевым словам.
        
        Args:
            text: текст документа в нижнем регистре
            
        Returns:
            tuple: (тип документа, уверенность)
        """
        # Ключевые слова для каждого типа документа
        keywords = {
            DocumentType.SERVICE_AGREEMENT: [
                "service agreement", "agreement", "services", "scope of services",
                "supplier", "client", "fees", "payment terms", "liability"
            ],
            DocumentType.NDA: [
                "non-disclosure", "nda", "confidential", "confidentiality",
                "proprietary information", "trade secrets"
            ],
            DocumentType.EMPLOYMENT_CONTRACT: [
                "employment", "employee", "employer", "salary", "compensation",
                "termination", "non-compete", "severance"
            ],
            DocumentType.TENANCY_AGREEMENT: [
                "tenancy", "lease", "landlord", "tenant", "rent", "deposit",
                "premises", "utilities"
            ],
        }
        
        # Подсчитываем совпадения для каждого типа
        scores = {}
        for doc_type, type_keywords in keywords.items():
            score = 0
            for keyword in type_keywords:
                if keyword in text:
                    score += 1
            
            # Нормализуем score (максимум 10 баллов)
            normalized_score = min(score / len(type_keywords), 1.0)
            scores[doc_type] = normalized_score
        
        # Находим тип с максимальным score
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            if best_type[1] > 0.3:  # Порог уверенности
                return best_type[0], best_type[1]
        
        # Если не нашли подходящий тип
        return DocumentType.UNKNOWN, 0.5
    
    def _find_key_clauses(self, text: str) -> List[str]:
        """
        Находит ключевые пункты в документе.
        
        Args:
            text: текст документа в нижнем регистре
            
        Returns:
            List[str]: список найденных ключевых пунктов
        """
        key_clauses = []
        
        # Список ключевых пунктов для поиска
        clause_keywords = [
            ("payment", ["payment", "fee", "invoice", "compensation"]),
            ("liability", ["liability", "indemnity", "damages", "warranty"]),
            ("termination", ["termination", "terminate", "expiration", "renewal"]),
            ("intellectual property", ["intellectual property", "ip", "copyright", "patent"]),
            ("confidentiality", ["confidential", "non-disclosure", "proprietary"]),
            ("jurisdiction", ["jurisdiction", "governing law", "venue", "dispute"]),
            ("scope", ["scope", "services", "deliverables", "milestones"]),
            ("warranty", ["warranty", "guarantee", "representation"]),
        ]
        
        for clause_name, keywords in clause_keywords:
            for keyword in keywords:
                if keyword in text:
                    key_clauses.append(clause_name)
                    break
        
        return key_clauses
