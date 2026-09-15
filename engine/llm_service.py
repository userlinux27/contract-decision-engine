"""
LLM Service Abstraction v1.0
Абстракция для LLM сервисов.

Реализация LLMServiceInterface.
"""

from typing import List, Dict
from engine.schemas import FindingInput
from engine.interfaces import LLMServiceInterface


class LLMService(LLMServiceInterface):
    """
    Абстрактный LLM сервис.
    """

    def __init__(self):
        pass

    def enrich_findings(self, findings: List[FindingInput]) -> List[Dict]:
        """
        Обогащает найденные факторы через LLM.

        Args:
            findings: список найденных факторов

        Returns:
            List[Dict]: обогащённые факторы с LLM объяснениями
        """
        enriched_findings = []

        for finding in findings:
            # Создаём копию finding как словарь
            finding_dict = finding.copy()

            # Добавляем LLM объяснения в зависимости от типа
            finding_type = finding_dict.get("type", "")

            if finding_type == "unlimited_liability":
                finding_dict["llm_reason"] = "Unlimited liability means the supplier could be responsible for unlimited financial damages."
                finding_dict["llm_impact"] = "This exposes the supplier to potentially catastrophic financial risk."
            elif finding_type == "payment_terms_unfavorable":
                finding_dict["llm_reason"] = "Extended payment terms create significant cash flow challenges."
                finding_dict["llm_impact"] = "The supplier may need to finance operations for extended periods before payment."
            elif finding_type == "ip_ownership_too_broad":
                finding_dict["llm_reason"] = "Broad IP transfer prevents reuse of tools and methodologies."
                finding_dict["llm_impact"] = "The supplier loses valuable assets that could be used for other clients."
            elif finding_type == "termination_unilateral":
                finding_dict["llm_reason"] = "Unilateral termination favors one party over the other."
                finding_dict["llm_impact"] = "Creates imbalance in the business relationship."
            elif finding_type == "jurisdiction_unfavorable":
                finding_dict["llm_reason"] = "Unfavorable jurisdiction increases legal costs."
                finding_dict["llm_impact"] = "Makes dispute resolution more expensive and inconvenient."
            else:
                finding_dict["llm_reason"] = "This clause may require review."
                finding_dict["llm_impact"] = "Consult with a legal professional for specific advice."

            enriched_findings.append(finding_dict)

        return enriched_findings


class OpenAIService(LLMService):
    """
    Реализация LLM сервиса с использованием OpenAI API.
    """

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        super().__init__()
        self.api_key = api_key
        self.model = model

    def enrich_findings(self, findings: List[FindingInput]) -> List[Dict]:
        """
        Обогащает найденные факторы через OpenAI API.

        Args:
            findings: список найденных факторов

        Returns:
            List[Dict]: обогащённые факторы с LLM объяснениями
        """
        # TODO: Реализовать реальную интеграцию с OpenAI API
        # Пока используем базовую реализацию
        return super().enrich_findings(findings)
