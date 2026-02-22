"""
Unit tests for Flask API endpoints using Flask test client.
No live server required.
"""

import io
import json
import pytest
import tempfile
from pathlib import Path

import pandas as pd
from flask import Flask

from nemt_parser.integrations.flask_adapter import nemt_bp, init_parser
from nemt_parser.core.models import ColumnMapping


# ---------------------------------------------------------------------------
# Flask test app fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def app(tmp_path):
    """Create a Flask test app with NEMT blueprint and a file-based SQLite DB
    so that data persists across requests within a single test."""
    db_path = tmp_path / "test.db"
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["NEMT_DATABASE_URL"] = f"sqlite:///{db_path}"
    app.config["UPLOAD_FOLDER"] = str(tmp_path / "uploads")
    app.config["DELETE_AFTER_PROCESSING"] = True
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    app.register_blueprint(nemt_bp)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def excel_bytes():
    """Build an in-memory Excel file and return raw bytes."""
    data = {
        "Patient Name": ["Jane Doe"],
        "Phone": ["3055551234"],
        "Medicaid #": ["MCD111"],
        "DOB": ["01/15/1960"],
        "Pick-up Address": ["100 NW 1st Ave"],
        "Pick-up City": ["Miami"],
        "Pick-up State": ["FL"],
        "Pick-up ZIP": ["33101"],
        "Drop-off Address": ["200 SW 2nd St"],
        "Drop-off City": ["Miami"],
        "Drop-off State": ["FL"],
        "Drop-off ZIP": ["33130"],
        "Appt Date": ["2025-06-15"],
        "Appt Time": ["10:30"],
        "Trip Type": ["Round Trip"],
        "Wheelchair?": ["No"],
        "Notes": ["Walker needed"],
    }
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf.read()


@pytest.fixture
def sample_mapping_dict():
    return {
        "clinic_id": "test_clinic",
        "clinic_name": "Test Medical Center",
        "patient_name": "Patient Name",
        "patient_phone": "Phone",
        "medicaid_id": "Medicaid #",
        "date_of_birth": "DOB",
        "pickup_address": "Pick-up Address",
        "pickup_city": "Pick-up City",
        "pickup_state": "Pick-up State",
        "pickup_zip": "Pick-up ZIP",
        "dropoff_address": "Drop-off Address",
        "dropoff_city": "Drop-off City",
        "dropoff_state": "Drop-off State",
        "dropoff_zip": "Drop-off ZIP",
        "appointment_date": "Appt Date",
        "appointment_time": "Appt Time",
        "trip_type": "Trip Type",
        "wheelchair": "Wheelchair?",
        "notes": "Notes",
    }


# =========================================================================
# POST /api/nemt/upload
# =========================================================================

class TestUploadEndpoint:
    def test_missing_file_returns_400(self, client):
        resp = client.post(
            "/api/nemt/upload",
            data={"clinic_id": "test"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False
        assert "No file" in body["error"]

    def test_missing_clinic_id_returns_400(self, client, excel_bytes):
        resp = client.post(
            "/api/nemt/upload",
            data={"file": (io.BytesIO(excel_bytes), "trips.xlsx")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert "clinic_id" in body["error"]

    def test_empty_filename_returns_400(self, client):
        resp = client.post(
            "/api/nemt/upload",
            data={
                "clinic_id": "test",
                "file": (io.BytesIO(b""), ""),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_first_upload_needs_mapping(self, client, excel_bytes):
        resp = client.post(
            "/api/nemt/upload",
            data={
                "clinic_id": "new_clinic",
                "clinic_name": "New Clinic",
                "file": (io.BytesIO(excel_bytes), "trips.xlsx"),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["needs_mapping"] is True
        assert "suggested_mapping" in body
        assert "detected_columns" in body

    def test_upload_with_saved_mapping(self, client, excel_bytes, sample_mapping_dict):
        # Step 1: save mapping
        save_resp = client.post(
            "/api/nemt/mapping/save",
            data=json.dumps(sample_mapping_dict),
            content_type="application/json",
        )
        assert save_resp.get_json()["success"] is True

        # Step 2: upload file
        resp = client.post(
            "/api/nemt/upload",
            data={
                "clinic_id": "test_clinic",
                "file": (io.BytesIO(excel_bytes), "trips.xlsx"),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["trips_parsed"] >= 1
        assert "trips" in body
        assert len(body["trips"]) >= 1

    def test_invalid_excel_returns_400(self, client):
        resp = client.post(
            "/api/nemt/upload",
            data={
                "clinic_id": "test",
                "file": (io.BytesIO(b"not-excel"), "bad.xlsx"),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400


# =========================================================================
# POST /api/nemt/mapping/save
# =========================================================================

class TestSaveMappingEndpoint:
    def test_save_mapping(self, client, sample_mapping_dict):
        resp = client.post(
            "/api/nemt/mapping/save",
            data=json.dumps(sample_mapping_dict),
            content_type="application/json",
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["clinic_id"] == "test_clinic"

    def test_save_invalid_mapping(self, client):
        resp = client.post(
            "/api/nemt/mapping/save",
            data=json.dumps({"bad": "data"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["success"] is False


# =========================================================================
# GET /api/nemt/mapping/<clinic_id>
# =========================================================================

class TestGetMappingEndpoint:
    def test_get_existing_mapping(self, client, sample_mapping_dict):
        client.post(
            "/api/nemt/mapping/save",
            data=json.dumps(sample_mapping_dict),
            content_type="application/json",
        )
        resp = client.get("/api/nemt/mapping/test_clinic")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["mapping"]["clinic_id"] == "test_clinic"

    def test_get_nonexistent_mapping_returns_404(self, client):
        resp = client.get("/api/nemt/mapping/ghost_clinic")
        assert resp.status_code == 404
        body = resp.get_json()
        assert body["success"] is False


# =========================================================================
# GET /api/nemt/clinics
# =========================================================================

class TestListClinicsEndpoint:
    def test_empty_clinic_list(self, client):
        resp = client.get("/api/nemt/clinics")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["count"] == 0
        assert body["clinics"] == []

    def test_clinic_list_after_save(self, client, sample_mapping_dict):
        client.post(
            "/api/nemt/mapping/save",
            data=json.dumps(sample_mapping_dict),
            content_type="application/json",
        )
        resp = client.get("/api/nemt/clinics")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["count"] >= 1


# =========================================================================
# GET /api/nemt/history
# =========================================================================

class TestHistoryEndpoint:
    def test_empty_history(self, client):
        resp = client.get("/api/nemt/history")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["uploads"] == []

    def test_history_after_upload(self, client, excel_bytes, sample_mapping_dict):
        # Save mapping first so upload succeeds and logs history
        client.post(
            "/api/nemt/mapping/save",
            data=json.dumps(sample_mapping_dict),
            content_type="application/json",
        )
        # Upload a file
        client.post(
            "/api/nemt/upload",
            data={
                "clinic_id": "test_clinic",
                "file": (io.BytesIO(excel_bytes), "trips.xlsx"),
            },
            content_type="multipart/form-data",
        )
        resp = client.get("/api/nemt/history")
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["uploads"]) >= 1

    def test_history_with_clinic_filter(self, client, excel_bytes):
        client.post(
            "/api/nemt/upload",
            data={
                "clinic_id": "clinic_x",
                "file": (io.BytesIO(excel_bytes), "trips.xlsx"),
            },
            content_type="multipart/form-data",
        )
        resp = client.get("/api/nemt/history?clinic_id=clinic_x")
        body = resp.get_json()
        assert body["success"] is True
        assert all(u["clinic_id"] == "clinic_x" for u in body["uploads"])

    def test_history_with_limit(self, client, excel_bytes):
        resp = client.get("/api/nemt/history?limit=5")
        assert resp.status_code == 200
