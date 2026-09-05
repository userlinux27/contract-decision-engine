"""
Rule Detector v1.2
Обнаружение факторов риска в документах.
Исправлено: предотвращение дублирования одинаковых findings.

Реализация RuleDetectorInterface.
"""

import re
from typing import List, Set, Tuple
from engine.schemas import ParsedDocument, FindingInput
from engine.interfaces import RuleDetectorInterface
from engine.catalog import SERVICE_AGREEMENT_FACTORS


class RuleDetector(RuleDetectorInterface):
    """
    Детектор правил/факторов риска на основе ключевых слов.
    """
    
    def __init__(self):
        # Паттерны для каждого типа фактора
        self.patterns = {
            "unlimited_liability": [
                r"unlimited liability",
                r"liability.*without.*limit",
                r"liable.*without.*limitation",
                r"full liability",
            ],
            "liability_capped": [
                r"liability.*capped",
                r"liability.*limited.*to",
                r"maximum liability",
                r"cap on liability",
            ],
            "payment_terms_unfavorable": [
                r"(\d{2,3})\s+days.*payment",
                r"payment.*(\d{2,3})\s+days",
                r"net\s+(\d{2,3})",
                r"within\s+(\d{2,3})\s+days",
            ],
            "payment_terms_standard": [
                r"15\s+days.*payment",
                r"payment.*15\s+days",
                r"net\s+15",
                r"within\s+15\s+days",
            ],
            "ip_ownership_too_broad": [
                r"all intellectual property",
                r"all rights.*belong.*client",
                r"exclusive.*ownership.*client",
                r"assign.*all.*rights",
            ],
            "ip_ownership_fair": [
                r"pre-existing.*materials",
                r"background.*ip",
                r"supplier.*retains",
                r"client.*license",
            ],
            "termination_unilateral": [
                r"client.*may.*terminate",
                r"either party.*may.*terminate",
                r"termination.*without cause",
                r"immediate termination",
            ],
            "termination_balanced": [
                r"mutual agreement",
                r"breach.*material",
                r"cure period",
                r"written notice",
            ],
            "jurisdiction_unfavorable": [
                r"jurisdiction.*client",
                r"governing law.*client",
                r"venue.*client",
                r"disputes.*client",
            ],
            "jurisdiction_neutral": [
                r"neutral jurisdiction",
                r"mutual agreement",
                r"arbitration",
                r"mediation",
            ],
        }
        
        # Предлагаемые формулировки для каждого типа
        self.suggested_rewrites = {
            "unlimited_liability": "Supplier's total liability shall not exceed the total fees paid by Client.",
            "payment_terms_unfavorable": "Client shall pay all invoices within 15 days of receipt.",
            "ip_ownership_too_broad": "Supplier retains rights to pre-existing materials and tools.",
            "termination_unilateral": "Either party may terminate with 30 days written notice.",
            "jurisdiction_unfavorable": "Disputes shall be resolved in a neutral jurisdiction.",
        }
        
        # Объяснения для каждого типа
        self.reasons = {
            "unlimited_liability": "Unlimited liability exposes supplier to catastrophic financial risk.",
            "liability_capped": "Capped liability provides reasonable protection for supplier.",
            "payment_terms_unfavorable": "Extended payment terms create cash flow challenges.",
            "payment_terms_standard": "Standard payment terms are balanced for both parties.",
            "ip_ownership_too_broad": "Broad IP transfer prevents reuse of tools and methodologies.",
            "ip_ownership_fair": "Fair IP terms protect both supplier's tools and client's deliverables.",
            "termination_unilateral": "Unilateral termination favors client over supplier.",
            "termination_balanced": "Balanced termination terms protect both parties.",
            "jurisdiction_unfavorable": "Unfavorable jurisdiction increases legal costs for supplier.",
            "jurisdiction_neutral": "Neutral jurisdiction provides fair dispute resolution.",
        }
    
    def detect(self, document: ParsedDocument) -> List[dict]:
        """
        Обнаруживает факторы риска в документе.
        
        Args:
            document: распарсенный документ
            
        Returns:
            List[dict]: найденные факторы риска как словари (не FindingInput)
        """
        findings = []
        text_lower = document.text.lower()
        
        # Разбиваем текст на предложения для поиска контекста
        sentences = self._split_into_sentences(document.text)
        
        # Множество для отслеживания уже найденных типов факторов
        # (чтобы избежать дублирования одного и того же типа)
        seen_factor_types: Set[str] = set()
        
        # Проверяем каждый тип фактора
        for factor_type, patterns in self.patterns.items():
            # Если уже нашли этот тип фактора, пропускаем
            if factor_type in seen_factor_types:
                continue
                
            # Ищем все паттерны для этого типа
            for pattern in patterns:
                matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
                
                # Если нашли совпадение
                if matches:
                    # Берем первое совпадение
                    match = matches[0]
                    
                    # Отмечаем что нашли этот тип фактора
                    seen_factor_types.add(factor_type)
                    
                    # Находим предложение с совпадением
                    context_sentence = self._find_context_sentence(
                        match.start(), sentences
                    )
                    
                    # Определяем номер пункта
                    clause = self._extract_clause_number(match.start(), document.text)
                    
                    # Определяем confidence на основе качества совпадения
                    confidence = self._calculate_confidence(match, pattern)
                    
                    # Создаём finding как словарь (не FindingInput)
                    finding = {
                        "type": factor_type,
                        "confidence": confidence,
                        "reason": self.reasons.get(factor_type, "Potential risk detected"),
                        "original_text": context_sentence,
                        "suggested_rewrite": self.suggested_rewrites.get(factor_type),
                        "clause": clause
                    }
                    
                    findings.append(finding)
                    break  # Прерываем поиск других паттернов для этого типа
        
        return findings
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Разбивает текст на предложения.
        
        Args:
            text: исходный текст
            
        Returns:
            List[str]: список предложений
        """
        # Простое разбиение по точкам, восклицательным и вопросительным знакам
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _find_context_sentence(self, position: int, sentences: List[str]) -> str:
        """
        Находит предложение содержащее указанную позицию.
        
        Args:
            position: позиция в тексте
            sentences: список предложений
            
        Returns:
            str: предложение содержащее позицию
        """
        current_pos = 0
        for sentence in sentences:
            sentence_len = len(sentence) + 1  # +1 для точки/пробела
            if current_pos <= position < current_pos + sentence_len:
                return sentence
            current_pos += sentence_len
        
        return sentences[0] if sentences else "Context not found"
    
    def _extract_clause_number(self, position: int, text: str) -> str:
        """
        Извлекает номер пункта содержащего указанную позицию.
        
        Args:
            position: позиция в тексте
            text: исходный текст
            
        Returns:
            str: номер пункта или "unknown"
        """
        # Ищем ближайший номер пункта перед позицией
        text_before = text[:position]
        
        # Паттерны для номеров пунктов: "1.", "1.1", "Article 1", "Section 1"
        patterns = [
            r'(\d+[\.\d]*)\s*\.',
            r'Article\s+(\d+)',
            r'Section\s+(\d+)',
            r'Clause\s+(\d+)',
        ]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text_before))
            if matches:
                return matches[-1].group(1)  # Последний найденный номер
        
        return "unknown"
    
    def _calculate_confidence(self, match: re.Match, pattern: str) -> float:
        """
        Рассчитывает confidence на основе качества совпадения.
        
        Args:
            match: объект совпадения regex
            pattern: использованный паттерн
            
        Returns:
            float: confidence от 0.0 до 1.0
        """
        # Базовый confidence
        confidence = 0.8
        
        # Увеличиваем confidence для точных совпадений
        if "\\b" in pattern:  # Границы слов
            confidence += 0.1
        
        # Увеличиваем для сложных паттернов
        if len(pattern) > 20:
            confidence += 0.05
        
        # Ограничиваем до 0.5-0.95
        return max(0.5, min(0.95, confidence))
