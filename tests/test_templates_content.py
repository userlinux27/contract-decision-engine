"""Pytest tests for template content verification."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

# All five template slugs from content/templates/
TEMPLATE_SLUGS = [
    "consulting-agreement",
    "freelance-agreement",
    "independent-contractor-agreement",
    "master-services-agreement-msa",
    "non-disclosure-agreement-nda",
]


@pytest.mark.parametrize("slug", TEMPLATE_SLUGS)
def test_template_page_returns_200(slug):
    """Each template page should return HTTP 200."""
    response = client.get(f"/templates/{slug}")
    assert response.status_code == 200, f"{slug}: expected 200, got {response.status_code}"


@pytest.mark.parametrize("slug", TEMPLATE_SLUGS)
def test_template_contains_key_clauses_section(slug):
    """Each template page should contain 'Key Clauses' section."""
    response = client.get(f"/templates/{slug}")
    assert "Key Clauses" in response.text, f"{slug}: missing 'Key Clauses' section"


@pytest.mark.parametrize("slug", TEMPLATE_SLUGS)
def test_template_contains_faq_section(slug):
    """Each template page should contain 'Frequently Asked Questions' section."""
    response = client.get(f"/templates/{slug}")
    assert "Frequently Asked Questions" in response.text, f"{slug}: missing 'FAQ' section"


@pytest.mark.parametrize("slug", TEMPLATE_SLUGS)
def test_template_contains_conversion_bridge(slug):
    """Each template page should contain the conversion bridge text."""
    response = client.get(f"/templates/{slug}")
    assert "Did the client send" in response.text, f"{slug}: missing conversion bridge text"


@pytest.mark.parametrize("slug", TEMPLATE_SLUGS)
def test_template_has_substantial_content(slug):
    """Each template page should have substantial HTML content (> 5000 chars)."""
    response = client.get(f"/templates/{slug}")
    assert len(response.text) > 5000, f"{slug}: content too short ({len(response.text)} chars)"