"""Website extraction and email discovery."""

from __future__ import annotations

import html
import re
import ssl
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen

from .config import CONTACT_PAGE_HINTS, DEFAULT_TIMEOUT_SECONDS, FUNCTIONAL_LOCAL_PARTS, GENERIC_LOCAL_PARTS, MAX_PAGES_PER_COMPANY, ROLE_PRIORITIES

EMAIL_RE = re.compile(
    r"(?<![A-Z0-9._%+-])([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})(?![A-Z0-9._%+-])",
    re.IGNORECASE,
)


def normalize_website(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not urlparse(url).scheme:
        url = "https://" + url
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    return urlunparse((parsed.scheme.lower(), netloc, path, "", "", ""))


def extract_domain(url: str) -> str:
    parsed = urlparse(normalize_website(url))
    host = parsed.hostname or ""
    if host.startswith("www."):
        host = host[4:]
    return host


def build_candidate_email(founder_name: str, domain: str) -> str:
    if not founder_name or not domain:
        return ""
    parts = [p for p in re.split(r"\s+", founder_name.strip()) if p]
    if len(parts) < 2:
        return ""
    first = re.sub(r"[^a-z]", "", parts[0].lower())
    last = re.sub(r"[^a-z]", "", parts[-1].lower())
    if not first or not last:
        return ""
    return f"{first}.{last}@{domain}"


def local_part_is_generic(email: str) -> bool:
    local = email.split("@", 1)[0].lower()
    return local in GENERIC_LOCAL_PARTS


def local_part_is_functional(email: str) -> bool:
    local = email.split("@", 1)[0].lower()
    return local in FUNCTIONAL_LOCAL_PARTS


def classify_email_type(email: str, candidate: bool = False) -> str:
    if candidate:
        return "candidate"
    if local_part_is_functional(email):
        return "functional"
    if local_part_is_generic(email):
        return "generic"
    return "personal"


@dataclass
class PageData:
    url: str
    title: str
    text: str
    html: str
    emails: set[str]
    links: set[str]
    category: str


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.in_title = False
        self.text_parts: list[str] = []
        self.emails: set[str] = set()
        self.links: set[str] = set()
        self._attrs: dict[str, str] = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self._attrs = attrs
        if tag.lower() == "title":
            self.in_title = True
        href = attrs.get("href", "")
        if href:
            self.links.add(href)
            if href.lower().startswith("mailto:"):
                self.emails.add(href.split(":", 1)[1].split("?", 1)[0].strip().lower())

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if not data:
            return
        clean = html.unescape(data)
        if self.in_title:
            self.title += clean.strip()
        self.text_parts.append(clean)
        for email in EMAIL_RE.findall(clean):
            self.emails.add(email.lower())

    @property
    def text(self):
        return " ".join(self.text_parts)


def _fetch(url: str) -> tuple[str, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; LeadResearchAgent/0.1)",
        "Accept": "text/html,application/xhtml+xml",
    }
    req = Request(url, headers=headers)
    ctx = ssl.create_default_context()
    try:
        with urlopen(req, timeout=DEFAULT_TIMEOUT_SECONDS, context=ctx) as response:
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "application/xhtml+xml"}:
                return "", response.geturl()
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace"), response.geturl()
    except (HTTPError, URLError, TimeoutError, ValueError, ConnectionResetError, OSError):
        return "", url


def _parse_page(url: str, html_text: str) -> PageData:
    parser = _PageParser()
    parser.feed(html_text)
    text = parser.text
    category = _page_category(url, parser.title, text)
    return PageData(
        url=url,
        title=parser.title.strip(),
        text=text,
        html=html_text,
        emails={e.lower() for e in parser.emails},
        links=set(parser.links),
        category=category,
    )


def _page_category(url: str, title: str, text: str) -> str:
    blob = f"{url} {title} {text}".lower()
    for hint in ("contact", "team", "about", "leadership", "people", "company", "privacy", "terms", "imprint", "impressum"):
        if hint in blob:
            return hint
    return "homepage"


def _internal_link(base_domain: str, base_url: str, href: str) -> str | None:
    href = href.strip()
    if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    host = parsed.hostname or ""
    if host.startswith("www."):
        host = host[4:]
    if host and host != base_domain:
        return None
    cleaned = parsed._replace(fragment="")
    return urlunparse(cleaned)


def discover_pages(website: str) -> list[PageData]:
    normalized = normalize_website(website)
    if not normalized:
        return []
    domain = extract_domain(normalized)
    candidates = [normalized]
    parsed = urlparse(normalized)
    root = f"{parsed.scheme}://{parsed.netloc}"
    for path in [
        "/contact",
        "/contact-us",
        "/about",
        "/team",
        "/people",
        "/leadership",
        "/company",
        "/privacy",
        "/terms",
        "/legal",
        "/imprint",
        "/impressum",
    ]:
        candidates.append(urljoin(root, path))

    seen: set[str] = set()
    pages: list[PageData] = []
    queue = [c for c in candidates if c not in seen]

    while queue and len(pages) < MAX_PAGES_PER_COMPANY:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        html_text, final_url = _fetch(current)
        if not html_text:
            continue
        page = _parse_page(final_url, html_text)
        pages.append(page)
        for href in page.links:
            internal = _internal_link(domain, final_url, href)
            if not internal or internal in seen:
                continue
            lower = internal.lower()
            if any(hint in lower for hint in CONTACT_PAGE_HINTS):
                queue.append(internal)

    return pages


def _role_score(page: PageData, founder_name: str) -> tuple[str, int, bool]:
    blob = f"{page.title} {page.text}".lower()
    found = founder_name and founder_name.lower() in blob
    best_role = ""
    best_score = 0
    for role, score in ROLE_PRIORITIES:
        if role in blob:
            best_role = role
            best_score = score
            break
    if not best_role and found:
        best_role = "founder/ceo"
        best_score = 30
    return best_role, best_score, bool(found)


def _role_display(role: str, founder_match: bool) -> str:
    if founder_match and not role:
        return "Founder / CEO"
    display_map = {
        "founder": "Founder",
        "ceo": "CEO",
        "owner": "Owner",
        "managing director": "Managing Director",
        "partner": "Partner",
        "director": "Director",
        "commercial director": "Commercial Director",
        "operations director": "Operations Director",
        "founder/ceo": "Founder / CEO",
    }
    return display_map.get(role, role.title() if role else "")


def _score_page(page: PageData, founder_name: str, email: str) -> int:
    score = 0
    if email:
        score += 30
    if page.category in {"contact", "team", "about", "leadership", "people", "company"}:
        score += 15
    elif page.category in {"privacy", "terms", "legal", "imprint", "impressum"}:
        score += 5
    else:
        score += 8
    role, role_score, founder_match = _role_score(page, founder_name)
    score += role_score
    if founder_match:
        score += 20
    if email and email.split("@", 1)[1].lower() == extract_domain(page.url).lower():
        score += 15
    if local_part_is_functional(email):
        score -= 25
    elif local_part_is_generic(email):
        score -= 25
    if email and email == build_candidate_email(founder_name, extract_domain(page.url)):
        score -= 40
    return max(0, min(100, score))


def find_website_contacts(company: str, founder_name: str, website: str) -> list[dict]:
    pages = discover_pages(website)
    domain = extract_domain(website)
    results: list[dict] = []
    seen_emails: set[str] = set()

    for page in pages:
        for email in sorted(page.emails):
            if not email:
                continue
            if email in seen_emails:
                continue
            seen_emails.add(email)
            email_domain = email.split("@", 1)[1].lower() if "@" in email else ""
            same_domain = bool(domain) and (email_domain == domain or email_domain.endswith("." + domain))
            role, role_score, founder_match = _role_score(page, founder_name)
            display_role = _role_display(role, founder_match)
            score = _score_page(page, founder_name, email)
            status = "verified" if same_domain else "unverified"
            email_type = classify_email_type(email)
            notes = []
            if page.category:
                notes.append(f"page={page.category}")
            if role:
                notes.append(f"role={role}")
            if founder_match:
                notes.append("founder_match=true")
            if same_domain:
                notes.append("same_domain=true")
            results.append(
                {
                    "company": company,
                    "website": website,
                    "contact_name": founder_name if founder_match else "",
                    "contact_role": display_role,
                    "email": email,
                    "email_type": email_type,
                    "verification_status": status,
                    "confidence": score,
                    "found_method": "website_html",
                    "source": "official_website",
                    "source_url": page.url,
                    "source_count": 1,
                    "notes": "; ".join(notes),
                    "page_title": page.title,
                    "page_category": page.category,
                    "candidate_email": "",
                    "verified": status == "verified",
                    "decision_maker": bool(founder_match or role_score >= 20),
                    "role_score": role_score,
                }
            )

    if not results and founder_name and domain:
        candidate = build_candidate_email(founder_name, domain)
        if candidate:
            results.append(
                {
                    "company": company,
                    "website": website,
                    "contact_name": founder_name,
                    "contact_role": "Founder / CEO",
                    "email": candidate,
                    "email_type": "candidate",
                    "verification_status": "candidate",
                    "confidence": 20,
                    "found_method": "name_domain_pattern",
                    "source": "pattern_guess",
                    "source_url": website,
                    "source_count": 0,
                    "notes": "candidate_only; not counted as reliable",
                    "page_title": "",
                    "page_category": "candidate",
                    "candidate_email": candidate,
                    "verified": False,
                    "decision_maker": True,
                    "role_score": 30,
                }
            )

    return results
