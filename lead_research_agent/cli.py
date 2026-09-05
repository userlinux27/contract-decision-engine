"""CLI entry point."""

from __future__ import annotations

import argparse

from .researcher import best_company_record, enrich_company, load_companies, summarize, write_prospects


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lead_research_agent", description="Lead Research Agent v0.1")
    parser.add_argument("--input", required=True, help="Input CSV with companies")
    parser.add_argument("--output", required=True, help="Output CSV with prospects")
    parser.add_argument("--limit", type=int, default=0, help="Process only the first N companies")
    return parser
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    companies = load_companies(args.input)
    if args.limit and args.limit > 0:
        companies = companies[: args.limit]

    all_records = []
    no_reliable_contact = 0
    for idx, company in enumerate(companies, start=1):
        try:
            records = enrich_company(company, use_optional_providers=True)
            best = best_company_record(records, company)
        except Exception as exc:
            best = best_company_record([], company)
            best.notes = f"error={exc.__class__.__name__}"
        all_records.append(best)
        if best.verification_status != "verified":
            no_reliable_contact += 1
        print(
            f"[{idx}/{len(companies)}] {company.company} | "
            f"Contact: {best.contact_name or company.founder_name or '-'} | "
            f"Role: {best.contact_role or '-'} | Email: {best.email or '-'} | "
            f"Type: {best.email_type or '-'} | DM: {'Y' if best.decision_maker else 'N'} | "
            f"Verified: {best.verification_status} | Lead score: {best.lead_score} | "
            f"Mailbox: {best.mailbox_quality}"
        )

    write_prospects(args.output, all_records)
    summary = summarize(all_records)
    print(
        f"Companies: {len(companies)} "
        f"Contacts found: {summary['contacts_found']} "
        f"Verified: {summary['verified']} "
        f"Quality A: {summary['quality_a']} "
        f"Quality B: {summary['quality_b']} "
        f"Quality C: {summary['quality_c']} "
        f"No reliable contact: {no_reliable_contact}"
    )
    return 0
