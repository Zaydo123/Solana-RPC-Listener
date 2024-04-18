# Pytest For Auth Module
import pytest
from fastapi.testclient import TestClient
from backend.main import app
client = TestClient(app)

def test_create_key():
    response = client.post("/api/key", json={"ip_whitelist": ["0.0.0.0"] })
    assert response.status_code == 200

def test_get_key():
    response = client.get("/api/key/1")
    assert response.status_code == 200

