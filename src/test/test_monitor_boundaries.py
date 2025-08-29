import pytest
from fastapi.testclient import TestClient

from src.app.main import app  # assuming unified entry exposes app

client = TestClient(app)

BASE = "/api/v1/monitor"

def test_start_stop_boundary_flow():
    # Start first time
    resp = client.post(f"{BASE}/start", json={"model_path": "yolo.pt", "camera_index": 0, "show_window": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"started", "already_running"}

    # Start again should give already_running
    resp2 = client.post(f"{BASE}/start", json={"model_path": "yolo.pt", "camera_index": 0, "show_window": False})
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "already_running"

    # Stop should return stopped or not_running depending on timing
    stop_resp = client.post(f"{BASE}/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] in {"stopped", "not_running"}

    # Stop again should be not_running
    stop_resp2 = client.post(f"{BASE}/stop")
    assert stop_resp2.status_code == 200
    assert stop_resp2.json()["status"] == "not_running"


def test_session_404():
    # Removing / using non-existent session id in status
    resp = client.get(f"{BASE}/status", params={"session_id": "does-not-exist"})
    assert resp.status_code == 404

    # Removing non existent session
    del_resp = client.delete(f"{BASE}/session/does-not-exist")
    assert del_resp.status_code == 404


def test_records_and_summary_after_stop():
    # Ensure a fresh session
    sid = "temp-boundary"
    start = client.post(f"{BASE}/start", params={"session_id": sid}, json={"model_path": "yolo.pt", "camera_index": 0, "show_window": False})
    assert start.status_code == 200
    client.post(f"{BASE}/stop", params={"session_id": sid})

    recs = client.get(f"{BASE}/records", params={"session_id": sid})
    assert recs.status_code == 200

    summary = client.get(f"{BASE}/summary", params={"session_id": sid})
    assert summary.status_code == 200

    # cleanup
    client.delete(f"{BASE}/session/{sid}")
