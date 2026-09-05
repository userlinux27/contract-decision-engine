"""
Base Decision Engine v1.0
Переиспользуемое ядро для всех будущих продуктов платформы.

Использование:
    engine = ServiceAgreementEngine()
    result = engine.decide(findings)
"""

from engine.catalog import DECISIONS, THRESHOLDS


class BaseDecisionEngine:
    """
    Базовый класс Decision Engine.

    Не содержит предметной логики — только алгоритм принятия решения.
    Предметная логика — в факторах и порогах, которые передаются при инициализации.

    Принцип работы:
    1. Принимает список найденных LLM факторов (findings)
    2. Суммирует веса с учётом confidence
    3. Определяет категорию решения по порогам
    4. Проверяет минимальный confidence для категории
    5. Возвращает решение + топ-3 причины
    """

    def __init__(self, factors: dict, thresholds: dict = None):
        """
        Args:
            factors: словарь факторов вида {type: {weight, severity, ...}}
            thresholds: словарь порогов вида {safe: int, changes: int}
        """
        self.factors = factors
        self.thresholds = thresholds or THRESHOLDS

    def decide(self, findings: list) -> dict:
        """
        Принимает список найденных факторов, возвращает решение.

        Args:
            findings: список dict с ключами:
                - type (str): тип фактора из catalog
                - confidence (float): 0.0–1.0
                - reason (str): объяснение
                - suggested_rewrite (str | None): безопасная формулировка
                - clause (str): номер пункта
                - original_text (str): исходный текст

        Returns:
            dict с ключами:
                - decision (str): safe_to_sign | sign_after_changes | do_not_sign
                - confidence (float): агрегированный уровень уверенности
                - top_reasons (list): топ-3 фактора по весу
                - all_findings (list): все найденные факторы
                - total_weight (int): суммарный вес
        """
        if not findings:
            return {
                "decision": "safe_to_sign",
                "confidence": 1.0,
                "top_reasons": [],
                "all_findings": [],
                "total_weight": 0,
            }

        # Суммируем веса с учётом confidence модели
        total_weight = 0
        weighted_findings = []

        for f in findings:
            factor_type = f.get("type")
            factor_config = self.factors.get(factor_type)

            if factor_config:
                base_weight = factor_config["weight"]
                llm_confidence = f.get("confidence", 0.5)

                # Если LLM не уверен — вес снижается пропорционально
                adjusted_weight = base_weight * llm_confidence

                total_weight += adjusted_weight
                weighted_findings.append(
                    {
                        **f,
                        "base_weight": base_weight,
                        "adjusted_weight": round(adjusted_weight, 1),
                        "severity": factor_config["severity"],
                        "explanation": factor_config.get("explanation", ""),
                        "has_suggested_wording": factor_config.get(
                            "has_suggested_wording", False
                        ),
                    }
                )

        # Нормализуем total_weight (округляем до целого)
        total_weight = round(total_weight)

        # Определяем предварительное решение по порогам
        if total_weight <= self.thresholds["safe"]:
            preliminary_decision = "safe_to_sign"
        elif total_weight <= self.thresholds["changes"]:
            preliminary_decision = "sign_after_changes"
        else:
            preliminary_decision = "do_not_sign"

        # Проверяем возможность suggested wording для sign_after_changes
        if preliminary_decision == "sign_after_changes":
            critical_findings = [
                f for f in weighted_findings if f["severity"] == "critical"
            ]
            # Если есть критические без suggested wording — повышаем до do_not_sign
            if critical_findings and not all(
                f.get("has_suggested_wording", False) for f in critical_findings
            ):
                preliminary_decision = "do_not_sign"

        # Проверяем минимальный confidence для категории
        decision_config = DECISIONS[preliminary_decision]
        min_confidence = decision_config["min_confidence"]

        # Агрегируем confidence: среднее арифметическое
        aggregated_confidence = sum(f["confidence"] for f in weighted_findings) / len(
            weighted_findings
        )
        aggregated_confidence = round(aggregated_confidence, 2)

        # Если confidence ниже минимального — понижаем решение
        if aggregated_confidence < min_confidence:
            if preliminary_decision == "safe_to_sign":
                preliminary_decision = "sign_after_changes"
            elif preliminary_decision == "sign_after_changes":
                # Не понижаем до do_not_sign только из-за низкого confidence
                pass

        # Сортируем по adjusted_weight и берём топ-3
        sorted_findings = sorted(
            weighted_findings, key=lambda f: f["adjusted_weight"], reverse=True
        )
        top_reasons = sorted_findings[:3]

        return {
            "decision": preliminary_decision,
            "confidence": aggregated_confidence,
            "top_reasons": [
                {
                    "factor": f["explanation"],
                    "weight": f["base_weight"],
                    "reason": f.get("reason", ""),
                }
                for f in top_reasons
            ],
            "all_findings": weighted_findings,
            "total_weight": total_weight,
        }


class ServiceAgreementEngine(BaseDecisionEngine):
    """
    Реализация Decision Engine для договоров оказания услуг.
    """

    def __init__(self):
        from engine.catalog import SERVICE_AGREEMENT_FACTORS

        super().__init__(factors=SERVICE_AGREEMENT_FACTORS)
