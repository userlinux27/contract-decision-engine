"""Scoring helpers for lead quality."""

from .config import QUALITY_THRESHOLDS


def mailbox_quality(email_type: str, verification_status: str) -> str:
    if verification_status == "candidate":
        return "D"
    if email_type == "personal":
        return "A"
    if email_type == "generic":
        return "B"
    if email_type == "functional":
        return "C"
    return "D"


def email_quality_score(source: str, verification_status: str, email_type: str) -> int:
    score = 0
    if verification_status in {"verified", "valid"}:
        score += 30
    if source == "official_website":
        score += 15
    if email_type == "personal":
        score += 10
    elif email_type == "generic":
        score += 5
    elif email_type == "functional":
        score -= 20
    return max(0, min(55, score))


def decision_maker_score(decision_maker: bool) -> int:
    return 40 if decision_maker else 0


def lead_score(decision_maker: bool, source: str, verification_status: str, email_type: str) -> int:
    return decision_maker_score(decision_maker) + email_quality_score(source, verification_status, email_type)


def normalize_score(score: int) -> int:
    return max(0, min(100, int(score)))


def is_reliable(verification_status: str, confidence: int) -> bool:
    return verification_status in {"verified", "valid"} and confidence >= 60


def lead_tier(score: int) -> str:
    if score >= QUALITY_THRESHOLDS["A"]:
        return "High"
    if score >= QUALITY_THRESHOLDS["B"]:
        return "Medium"
    if score >= QUALITY_THRESHOLDS["C"]:
        return "Low"
    return "Needs verification"
