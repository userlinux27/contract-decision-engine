"""
Decision Catalogue v0.1
Каталог факторов риска и порогов для Decision Engine.

Используется Decision Engine для определения весов и серьёзности факторов.
"""

# Пороги для принятия решений
THRESHOLDS = {
    "safe": -10,      # Вес <= -10 → Safe to sign
    "changes": 20,    # Вес <= 20 → Sign after changes
    # Вес > 20 → Do not sign
}

# Конфигурация решений
DECISIONS = {
    "safe_to_sign": {
        "display_name": "✅ Ready to Sign",
        "min_confidence": 0.7,
    },
    "sign_after_changes": {
        "display_name": "🟡 Review Recommended",
        "min_confidence": 0.6,
    },
    "do_not_sign": {
        "display_name": "🔴 High Risk",
        "min_confidence": 0.5,
    },
}

# Факторы для договоров оказания услуг
SERVICE_AGREEMENT_FACTORS = {
    "unlimited_liability": {
        "weight": 30,
        "severity": "critical",
        "explanation": "Unlimited liability",
        "has_suggested_wording": True,
    },
    "liability_capped": {
        "weight": -5,
        "severity": "low",
        "explanation": "Liability is capped",
        "has_suggested_wording": False,
    },
    "payment_terms_unfavorable": {
        "weight": 20,
        "severity": "medium",
        "explanation": "Payment terms favor client",
        "has_suggested_wording": True,
    },
    "payment_terms_standard": {
        "weight": -3,
        "severity": "low",
        "explanation": "Payment terms are balanced",
        "has_suggested_wording": False,
    },
    "ip_ownership_too_broad": {
        "weight": 25,
        "severity": "critical",
        "explanation": "IP ownership too broad",
        "has_suggested_wording": True,
    },
    "ip_ownership_fair": {
        "weight": -4,
        "severity": "low",
        "explanation": "IP ownership is fair",
        "has_suggested_wording": False,
    },
    "termination_unilateral": {
        "weight": 15,
        "severity": "medium",
        "explanation": "Unilateral termination",
        "has_suggested_wording": True,
    },
    "termination_balanced": {
        "weight": -2,
        "severity": "low",
        "explanation": "Termination terms are balanced",
        "has_suggested_wording": False,
    },
    "jurisdiction_unfavorable": {
        "weight": 10,
        "severity": "medium",
        "explanation": "Jurisdiction favors client",
        "has_suggested_wording": True,
    },
    "jurisdiction_neutral": {
        "weight": -1,
        "severity": "low",
        "explanation": "Jurisdiction is neutral",
        "has_suggested_wording": False,
    },
}

# Маппинг типов документов
DOCUMENT_TYPES = {
    "service_agreement": {
        "display_name": "Service Agreement",
        "factors": SERVICE_AGREEMENT_FACTORS,
        "supported": True,
    },
    "nda": {
        "display_name": "NDA",
        "factors": {},
        "supported": False,
    },
    "employment_contract": {
        "display_name": "Employment Contract",
        "factors": {},
        "supported": False,
    },
    "tenancy_agreement": {
        "display_name": "Tenancy Agreement",
        "factors": {},
        "supported": False,
    },
    "unknown": {
        "display_name": "Unknown Document",
        "factors": {},
        "supported": False,
    },
}
