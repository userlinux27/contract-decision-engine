"""Data models for the lead research agent."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompanyRow:
    company: str
    country: str
    type: str
    founder_name: str
    linkedin_url: str
    website: str
    hook: str = ""


@dataclass
class ProspectRecord:
    company: str
    country: str
    type: str
    website: str
    contact_name: str = ""
    contact_role: str = ""
    linkedin_url: str = ""
    email: str = ""
    email_type: str = ""
    verification_status: str = "candidate"
    confidence: int = 0
    mailbox_quality: str = "D"
    email_quality_score: int = 0
    lead_score: int = 0
    lead_tier: str = "Needs verification"
    found_method: str = ""
    source: str = ""
    source_url: str = ""
    source_count: int = 0
    notes: str = ""
    candidate_email: str = ""
    verified: bool = False
    hunter_confidence: Optional[int] = None
    decision_maker: bool = False
    decision_maker_score: int = 0
    page_title: str = ""
    page_category: str = ""
    role_score: int = 0
    source_rank: int = 0
    evidence: list[str] = field(default_factory=list)
