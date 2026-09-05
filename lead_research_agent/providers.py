"""Optional external providers."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import HUNTER_TIMEOUT_SECONDS


@dataclass
class ProviderHit:
    email: str
    source: str
    source_url: str
    verification_status: str
    confidence: int
    found_method: str
    notes: str = ""


class OptionalProvider:
    name = "provider"

    def enabled(self) -> bool:
        return False

    def lookup(self, company: str, domain: str, contact_name: str) -> List[ProviderHit]:
        return []


class HunterProvider(OptionalProvider):
    name = "hunter"

    def enabled(self) -> bool:
        return bool(os.getenv("HUNTER_API_KEY"))

    def _get(self, path: str, params: dict) -> dict:
        api_key = os.getenv("HUNTER_API_KEY", "").strip()
        if not api_key:
            return {}
        params = {**params, "api_key": api_key}
        url = f"https://api.hunter.io/v2/{path}?{urlencode(params)}"
        req = Request(url, headers={"Accept": "application/json", "User-Agent": "LeadResearchAgent/0.1"})
        with urlopen(req, timeout=HUNTER_TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8", errors="replace")
        return json.loads(payload)

    def _verify(self, email: str) -> tuple[str, int]:
        data = self._get("email-verifier", {"email": email})
        result = data.get("data", {}) if isinstance(data, dict) else {}
        status = (result.get("status") or "unknown").lower()
        score = int(result.get("score") or 0)
        return status, score

    def lookup(self, company: str, domain: str, contact_name: str) -> List[ProviderHit]:
        if not self.enabled() or not domain:
            return []

        hits: List[ProviderHit] = []
        parts = [p for p in contact_name.split() if p]
        first_name = parts[0] if parts else ""
        last_name = parts[-1] if len(parts) > 1 else ""

        if first_name and last_name:
            data = self._get(
                "email-finder",
                {"domain": domain, "first_name": first_name, "last_name": last_name},
            )
            result = data.get("data", {}) if isinstance(data, dict) else {}
            email = (result.get("email") or "").strip().lower()
            if email:
                status, score = self._verify(email)
                hits.append(
                    ProviderHit(
                        email=email,
                        source="hunter",
                        source_url=result.get("sources", [{}])[0].get("uri", f"https://{domain}"),
                        verification_status=status,
                        confidence=score or int(result.get("score") or 0) or 60,
                        found_method="hunter_email_finder",
                        notes=f"status={status}; score={score}",
                    )
                )
                return hits

        data = self._get("domain-search", {"domain": domain, "limit": 5})
        result = data.get("data", {}) if isinstance(data, dict) else {}
        emails = result.get("emails", []) if isinstance(result, dict) else []
        for item in emails[:5]:
            email = (item.get("value") or "").strip().lower()
            if not email:
                continue
            status, score = self._verify(email)
            hits.append(
                ProviderHit(
                    email=email,
                    source="hunter",
                    source_url=item.get("sources", [{}])[0].get("uri", f"https://{domain}"),
                    verification_status=status,
                    confidence=score or int(item.get("score") or 0) or 50,
                    found_method="hunter_domain_search",
                    notes=f"status={status}; score={score}",
                )
            )
        return hits
