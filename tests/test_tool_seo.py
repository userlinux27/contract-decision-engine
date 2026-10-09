"""Pytest tests for SEO meta tags on the Contract Risk Checker tool page."""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_tool_page_returns_200():
    """Tool page should return HTTP 200."""
    response = client.get("/tools/contract-risk-checker")
    assert response.status_code == 200


def test_tool_page_has_title():
    """Tool page should have a proper title tag."""
    response = client.get("/tools/contract-risk-checker")
    assert "<title>Free Contract Risk Checker" in response.text


def test_tool_page_has_meta_description():
    """Tool page should have meta description."""
    response = client.get("/tools/contract-risk-checker")
    assert 'name="description"' in response.text
    assert "free risk check" in response.text.lower()


def test_tool_page_has_canonical_url():
    """Tool page should have canonical URL."""
    response = client.get("/tools/contract-risk-checker")
    assert 'rel="canonical"' in response.text
    assert "/tools/contract-risk-checker" in response.text


def test_tool_page_has_og_tags():
    """Tool page should have Open Graph meta tags."""
    response = client.get("/tools/contract-risk-checker")
    assert 'property="og:title"' in response.text
    assert 'property="og:description"' in response.text
    assert 'property="og:type"' in response.text
    assert 'property="og:url"' in response.text


def test_tool_page_has_twitter_card():
    """Tool page should have Twitter card meta tag."""
    response = client.get("/tools/contract-risk-checker")
    assert 'name="twitter:card"' in response.text
    assert 'content="summary_large_image"' in response.text


def test_tool_page_has_og_title_content():
    """Tool page OG title should have expected content."""
    response = client.get("/tools/contract-risk-checker")
    assert 'property="og:title"' in response.text
    assert "Free Contract Risk Checker" in response.text


def test_tool_page_has_og_description_content():
    """Tool page OG description should have expected content."""
    response = client.get("/tools/contract-risk-checker")
    assert 'property="og:description"' in response.text
    assert "free risk check" in response.text.lower()