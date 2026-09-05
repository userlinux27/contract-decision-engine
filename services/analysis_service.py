"""
Analysis Service v1.0
Оркестрация полного pipeline анализа контрактов.

Отвечает за:
- Координацию всех этапов анализа
- Вызов существующих модулей pipeline
- Обработка ошибок на каждом этапе
- Формирование итогового результата
"""

import logging
from typing import Dict
from datetime import datetime

from engine.schemas import (
    ParsedDocument, ClassificationResult, AnalysisResult,
    DecisionOutput
)
from engine.pdf_parser import PDFParser
from engine.classifier import DocumentClassifier
from engine.rule_detector import RuleDetector
from engine.decision_engine import ServiceAgreementEngine
from engine.llm_service import LLMService

from services.task_service import TaskStatus

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisService:
    """Сервис анализа контрактов."""
    
    def __init__(self, task_service):
        """
        Args:
            task_service: сервис управления задачами
        """
        self.task_service = task_service
        self.parser = PDFParser()
        self.classifier = DocumentClassifier()
        self.rule_detector = RuleDetector()
        self.decision_engine = ServiceAgreementEngine()
        self.llm_service = LLMService()
    
    async def analyze_contract(self, task_id: str, filepath: str):
        """
        Выполняет полный анализ контракта.
        
        Args:
            task_id: идентификатор задачи
            filepath: путь к PDF файлу
        """
        try:
            logger.info(f"[ANALYZE] task={task_id} started analysis")
            
            # 1. Парсинг документа
            self.task_service.update_progress(
                task_id=task_id,
                progress=10,
                message="Reading document..."
            )
            
            parsed_document = await self._parse_document(filepath, task_id)
            
            # 2. Классификация документа
            self.task_service.update_progress(
                task_id=task_id,
                progress=30,
                message="Classifying document..."
            )
            
            classification = await self._classify_document(parsed_document, task_id)
            
            # 3. Поиск факторов (rule detection)
            self.task_service.update_progress(
                task_id=task_id,
                progress=50,
                message="Checking key terms..."
            )
            
            findings = await self._detect_factors(parsed_document, task_id)
            
            # 4. Принятие решения
            self.task_service.update_progress(
                task_id=task_id,
                progress=70,
                message="Preparing decision..."
            )
            
            decision_result = await self._make_decision(findings, task_id)
            
            # 5. Обогащение через LLM
            self.task_service.update_progress(
                task_id=task_id,
                progress=90,
                message="Generating explanations..."
            )
            
            enriched_result = await self._enrich_with_llm(decision_result, task_id)
            
            # 6. Формирование итогового результата
            result = self._format_result(
                parsed_document=parsed_document,
                classification=classification,
                findings=findings,
                decision_result=enriched_result,
                filepath=filepath
            )
            
            # 7. Завершение задачи
            self.task_service.complete_task(task_id=task_id, result=result)
            logger.info(f"[ANALYZE] task={task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"[ANALYZE] task={task_id} FAILED: {str(e)}")
            self.task_service.fail_task(
                task_id=task_id,
                error=f"Analysis failed: {str(e)}"
            )
            raise
    
    async def _parse_document(self, filepath: str, task_id: str) -> ParsedDocument:
        """Парсит PDF документ."""
        try:
            logger.info(f"[ANALYZE] task={task_id} parsing started")
            document = self.parser.parse(filepath)
            logger.info(f"[ANALYZE] task={task_id} parsing completed")
            return document
        except Exception as e:
            logger.error(f"[ANALYZE] task={task_id} parsing failed: {str(e)}")
            raise
    
    async def _classify_document(self, document: ParsedDocument, task_id: str) -> ClassificationResult:
        """Классифицирует документ."""
        try:
            logger.info(f"[ANALYZE] task={task_id} classification started")
            classification = self.classifier.classify(document)
            logger.info(f"[ANALYZE] task={task_id} classification={classification.document_type}")
            return classification
        except Exception as e:
            logger.error(f"[ANALYZE] task={task_id} classification failed: {str(e)}")
            raise
    
    async def _detect_factors(self, document: ParsedDocument, task_id: str) -> list:
        """Обнаруживает факторы риска."""
        try:
            logger.info(f"[ANALYZE] task={task_id} rule detection started")
            findings = self.rule_detector.detect(document)
            logger.info(f"[ANALYZE] task={task_id} detected {len(findings)} factors")
            return findings
        except Exception as e:
            logger.error(f"[ANALYZE] task={task_id} rule detection failed: {str(e)}")
            raise
    
    async def _make_decision(self, findings: list, task_id: str) -> Dict:
        """Принимает решение на основе факторов."""
        try:
            logger.info(f"[ANALYZE] task={task_id} decision engine started")
            decision_result = self.decision_engine.decide(findings)
            logger.info(f"[ANALYZE] task={task_id} decision={decision_result['decision']}")
            return decision_result  # Возвращаем dict, а не DecisionOutput
        except Exception as e:
            logger.error(f"[ANALYZE] task={task_id} decision engine failed: {str(e)}")
            raise
    
    async def _enrich_with_llm(self, decision_result: Dict, task_id: str) -> Dict:
        """Обогащает результат через LLM."""
        try:
            logger.info(f"[ANALYZE] task={task_id} LLM enrichment started")
            
            # Конвертируем findings в список словарей для LLM
            findings_dicts = []
            for finding in decision_result.get("all_findings", []):
                # Создаём FindingInput из данных
                findings_dicts.append({
                    "type": finding.get("type", ""),
                    "confidence": finding.get("confidence", 0.5),
                    "reason": finding.get("reason", ""),
                    "original_text": finding.get("original_text", ""),
                    "suggested_rewrite": finding.get("suggested_rewrite")
                })
            
            # Обогащаем через LLM
            enriched_findings = self.llm_service.enrich_findings(findings_dicts)
            
            # Обновляем результат
            decision_result["all_findings"] = enriched_findings
            
            logger.info(f"[ANALYZE] task={task_id} LLM enrichment completed")
            return decision_result
            
        except Exception as e:
            logger.error(f"[ANALYZE] task={task_id} LLM enrichment failed: {str(e)}")
            # Не падаем если LLM не работает, возвращаем исходный результат
            return decision_result
    
    def _format_result(
        self,
        parsed_document: ParsedDocument,
        classification: ClassificationResult,
        findings: list,
        decision_result: Dict,
        filepath: str
    ) -> Dict:
        """
        Формирует итоговый результат для frontend.
        """
        # Формируем pipeline информацию
        pipeline_info = {
            "text_length": len(parsed_document.text),
            "word_count": len(parsed_document.text.split()),
            "pages": parsed_document.pages,
            "language": parsed_document.language,
            "estimated_reading_time_min": parsed_document.estimated_reading_time_min,
            "processing_time_sec": 0,  # TODO: рассчитать реальное время
            "parser": "pdf_parser_v1.0"
        }
        
        # Формируем decision labels
        decision_labels = {
            "safe_to_sign": "✅ Ready to Sign",
            "sign_after_changes": "🟡 Review Recommended",
            "do_not_sign": "🔴 High Risk"
        }
        
        # Создаём DecisionOutput из словаря
        decision_output = DecisionOutput(**decision_result)
        
        # Создаём AnalysisResult
        result = AnalysisResult(
            classification=classification,
            pipeline=pipeline_info,
            decision=decision_result.get("decision", "safe_to_sign"),
            decision_details=decision_output,
            decision_labels=decision_labels
        )
        
        return result.dict()
