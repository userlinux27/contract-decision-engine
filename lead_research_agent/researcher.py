"""Lead research orchestration."""

from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path

from .models import CompanyRow, ProspectRecord
from .providers import HunterProvider
from .scorer import mailbox_quality, lead_score, lead_tier, normalize_score
from .website_finder import find_website_contacts, normalize_website, extract_domain, classify_email_type


OUTPUT_COLUMNS = [
    "company",
    "country",
    "type",
    "website",
    "contact_name",
    "contact_role",
    "linkedin_url",
    "email",
    "email_type",
    "verification_status",
    "confidence",
    "mailbox_quality",
    "email_quality_score",
    "decision_maker_score",
    "lead_score",
    "lead_tier",
    "found_method",
    "source",
    "source_url",
    "source_count",
    "hunter_confidence",
    "decision_maker",
    "verified",
    "candidate_email",
    "notes",
]


def load_companies(path: str) -> list[CompanyRow]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[CompanyRow] = []
        for raw in reader:
            rows.append(
                CompanyRow(
                    company=(raw.get("company") or raw.get("Company") or "").strip(),
                    country=(raw.get("country") or raw.get("Country") or "").strip(),
                    type=(raw.get("type") or raw.get("Type") or "").strip(),
                    founder_name=(raw.get("founder_name") or raw.get("Founder / CEO") or raw.get("Founder / CEO ") or "").strip(),
                    linkedin_url=(raw.get("linkedin_url") or raw.get("LinkedIn Profile") or raw.get("LinkedIn") or "").strip(),
                    website=(raw.get("website") or raw.get("Website") or raw.get("Website (для проверки)") or "").strip(),
                    hook=(raw.get("hook") or raw.get("Hook") or "").strip(),
                )
            )
        return rows


def _finalize_record(row: CompanyRow, item: dict) -> ProspectRecord:
    score = normalize_score(item.get("confidence", 0))
    verification_status = item.get("verification_status", "candidate")
    email = (item.get("email", "") or "").strip().lower()
    email_type = item.get("email_type") or classify_email_type(email, verification_status == "candidate")
    mailbox = mailbox_quality(email_type, verification_status)
    lead = lead_score(bool(item.get("decision_maker", False)), item.get("source", ""), verification_status, email_type)
    return ProspectRecord(
        company=row.company,
        country=row.country,
        type=row.type,
        website=normalize_website(row.website) or row.website,
        contact_name=item.get("contact_name") or row.founder_name,
        contact_role=item.get("contact_role", ""),
        linkedin_url=row.linkedin_url,
        email=item.get("email", ""),
        email_type=email_type,
        verification_status=verification_status,
        confidence=score,
        mailbox_quality=mailbox,
        email_quality_score=max(0, lead - (40 if item.get("decision_maker", False) else 0)),
        lead_score=lead,
        lead_tier=lead_tier(lead),
        found_method=item.get("found_method", ""),
        source=item.get("source", ""),
        source_url=item.get("source_url", ""),
        source_count=int(item.get("source_count", 0) or 0),
        notes=item.get("notes", ""),
        candidate_email=item.get("candidate_email", ""),
        verified=bool(item.get("verified", False)) or verification_status in {"verified", "valid"},
        hunter_confidence=item.get("hunter_confidence"),
        decision_maker=bool(item.get("decision_maker", False)),
        decision_maker_score=40 if item.get("decision_maker", False) else 0,
        page_title=item.get("page_title", ""),
        page_category=item.get("page_category", ""),
        role_score=int(item.get("role_score", 0) or 0),
    )


def _rank_record(record: ProspectRecord) -> tuple:
    reliable = record.verification_status == "verified"
    return (
        0 if reliable else 1,
        0 if record.mailbox_quality == "A" else 1 if record.mailbox_quality == "B" else 2 if record.mailbox_quality == "C" else 3,
        -record.lead_score,
        -record.confidence,
    )


def enrich_company(row: CompanyRow, use_optional_providers: bool = True) -> list[ProspectRecord]:
    website = normalize_website(row.website)
    domain = extract_domain(website)
    website_hits = find_website_contacts(row.company, row.founder_name, website)
    records = [_finalize_record(row, hit) for hit in website_hits]

    if use_optional_providers and domain and row.founder_name:
        provider = HunterProvider()
        if provider.enabled():
            for hit in provider.lookup(row.company, domain, row.founder_name):
                verified = hit.verification_status in {"verified", "valid"}
                hit_map = {
                    "company": row.company,
                    "website": website,
                    "contact_name": row.founder_name,
                    "contact_role": "Founder / CEO",
                    "email": hit.email,
                    "email_type": classify_email_type(hit.email, hit.verification_status == "candidate"),
                    "verification_status": hit.verification_status,
                    "confidence": hit.confidence,
                    "found_method": hit.found_method,
                    "source": hit.source,
                    "source_url": hit.source_url,
                    "source_count": 1,
                    "notes": hit.notes,
                    "candidate_email": "",
                    "verified": verified,
                    "decision_maker": True,
                    "hunter_confidence": hit.confidence,
                    "page_title": "",
                    "page_category": provider.name,
                    "role_score": 30,
                }
                records.append(_finalize_record(row, hit_map))

    best_by_email: dict[str, ProspectRecord] = {}
    for record in records:
        key = record.email.lower()
        current = best_by_email.get(key)
        if current is None or _rank_record(record) < _rank_record(current):
            best_by_email[key] = record

    return sorted(best_by_email.values(), key=_rank_record)


def best_company_record(records: list[ProspectRecord], row: CompanyRow) -> ProspectRecord:
    if records:
        return sorted(records, key=_rank_record)[0]
    placeholder = ProspectRecord(
        company=row.company,
        country=row.country,
        type=row.type,
        website=normalize_website(row.website) or row.website,
        contact_name=row.founder_name,
        contact_role="",
        linkedin_url=row.linkedin_url,
        email="",
        email_type="candidate",
        verification_status="candidate",
        confidence=0,
        mailbox_quality="D",
        email_quality_score=0,
        lead_score=0,
        lead_tier="Needs verification",
        found_method="no_contact",
        source="",
        source_url="",
        source_count=0,
        notes="no reliable contact found",
        candidate_email="",
        verified=False,
        hunter_confidence=None,
        decision_maker=False,
        decision_maker_score=0,
        page_title="",
        page_category="",
        role_score=0,
    )
    return placeholder


def write_prospects(path: str, records: list[ProspectRecord]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for record in records:
            data = asdict(record)
            row = {column: data.get(column, "") for column in OUTPUT_COLUMNS}
            writer.writerow(row)


def summarize(records: list[ProspectRecord]) -> dict[str, int]:
    summary = {
        "contacts_found": 0,
        "verified": 0,
        "quality_a": 0,
        "quality_b": 0,
        "quality_c": 0,
        "quality_d": 0,
    }
    for record in records:
        if record.verification_status == "verified":
            summary["contacts_found"] += 1
            summary["verified"] += 1
        if record.mailbox_quality == "A":
            summary["quality_a"] += 1
        elif record.mailbox_quality == "B":
            summary["quality_b"] += 1
        elif record.mailbox_quality == "C":
            summary["quality_c"] += 1
        else:
            summary["quality_d"] += 1
    return summary
