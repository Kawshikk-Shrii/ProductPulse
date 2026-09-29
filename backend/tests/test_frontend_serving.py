"""
Test that frontend files are correctly located and served by FastAPI.
"""

from fastapi.testclient import TestClient
from backend.app import app


def test_serve_index_html():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "ProductPulse" in response.text
    assert "AI Product Operations" in response.text
    assert "lifecycle-bar" in response.text
    # Verify memory-changed-panel is strictly hidden on initial page load
    assert 'class="card memory-changed-panel hidden"' in response.text


def test_serve_static_assets():
    client = TestClient(app)
    css_resp = client.get("/static/css/style.css")
    assert css_resp.status_code == 200
    assert "--bg-app" in css_resp.text

    js_resp = client.get("/static/js/app.js")
    assert js_resp.status_code == 200
    assert "ProductPulse Frontend Controller" in js_resp.text
    # Verify challenge mode gating logic is present in JS
    assert "isChallengeMode" in js_resp.text
