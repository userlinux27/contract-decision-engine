"""Configuration for the lead research agent."""

DEFAULT_TIMEOUT_SECONDS = 4
MAX_PAGES_PER_COMPANY = 2
HUNTER_TIMEOUT_SECONDS = 12

ROLE_PRIORITIES = [
    ("founder", 30),
    ("ceo", 30),
    ("owner", 28),
    ("managing director", 28),
    ("partner", 20),
    ("director", 15),
    ("commercial director", 15),
    ("operations director", 15),
]

CONTACT_PAGE_HINTS = [
    "contact",
    "about",
    "team",
    "leadership",
    "company",
    "people",
    "who-we-are",
    "who-we-are",
    "privacy",
    "terms",
    "legal",
    "imprint",
    "impressum",
    "people",
]

GENERIC_LOCAL_PARTS = {
    "hi",
    "info",
    "hello",
    "contact",
    "contactus",
    "enquiries",
    "inquiries",
    "office",
    "sales",
    "support",
    "team",
    "mail",
    "admin",
    "marketing",
    "careers",
    "jobs",
    "press",
    "media",
    "hr",
    "recruitment",
    "billing",
    "accounts",
    "partnerships",
}

FUNCTIONAL_LOCAL_PARTS = {
    "careers",
    "jobs",
    "support",
    "billing",
    "accounts",
    "hr",
    "recruitment",
    "press",
    "media",
    "partnerships",
    "sales",
    "legal",
    "privacy",
    "office",
}

QUALITY_THRESHOLDS = {
    "A": 90,
    "B": 75,
    "C": 60,
}
