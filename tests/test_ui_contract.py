"""Test UI contract compliance - ensure frontend and backend stay in sync.

These tests use the exact payload format sent by static/app.js to verify
the API endpoints return the expected response structure.
"""

import pytest
from fastapi.testclient import TestClient
import tempfile
from pathlib import Path

from src.trajgen.config import VehicleConfig
from src.trajgen.sweep import ReachabilitySweep
from src.trajgen.feasibility import FeasibilityChecker
from src.trajgen.api import app, app_state


@pytest.fixture(scope="module")
def client():
    """Create test client with initialized app state."""
    config = VehicleConfig()
    
    # Use smaller sweep for faster tests
    config['sweep']['launch_angle_step_deg'] = 5
    config['sweep']['burn_param_step'] = 0.2
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sweep = ReachabilitySweep(config, cache_dir=Path(tmpdir))
        sweep.build()
        checker = FeasibilityChecker(config, sweep)
        
        app_state['config'] = config
        app_state['sweep'] = sweep
        app_state['checker'] = checker
        
        with TestClient(app) as test_client:
            yield test_client
        
        # Clean up
        app_state['config'] = None
        app_state['sweep'] = None
        app_state['checker'] = None


class TestFeasibilityEndpointUIContract:
    """Test /api/feasibility with exact UI payload format."""
    
    def test_feasible_case_all_fields(self, client):
        """Test feasible case returns all fields the UI expects.
        
        This is the exact payload format from static/app.js lines 250-252.
        UI expects: feasible, reasons, peak_g_load, peak_heat_flux_w_cm2,
        distance_to_envelope_km (lines 319-334).
        """
        # Exact format from frontend: {launch: {lat, lon}, landing: {lat, lon}}
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify all required fields exist
        assert "feasible" in data, "Missing 'feasible' field"
        assert "reasons" in data, "Missing 'reasons' field"
        assert "peak_g_load" in data, "Missing 'peak_g_load' field"
        assert "peak_heat_flux_w_cm2" in data, "Missing 'peak_heat_flux_w_cm2' field"
        assert "distance_to_envelope_km" in data, "Missing 'distance_to_envelope_km' field"
        assert "range_km" in data, "Missing 'range_km' field"
        assert "azimuth_deg" in data, "Missing 'azimuth_deg' field"
        
        # Verify types
        assert isinstance(data["feasible"], bool), "feasible must be bool"
        assert isinstance(data["reasons"], list), "reasons must be list"
        assert len(data["reasons"]) > 0, "reasons must not be empty"
        
        # Check numeric fields (should exist for feasible cases)
        if data["feasible"]:
            assert data["peak_g_load"] is not None, "peak_g_load should not be None for feasible case"
            assert data["peak_heat_flux_w_cm2"] is not None, "peak_heat_flux_w_cm2 should not be None"
            assert isinstance(data["peak_g_load"], (int, float)), "peak_g_load must be numeric"
            assert isinstance(data["peak_heat_flux_w_cm2"], (int, float)), "peak_heat_flux_w_cm2 must be numeric"
        
        assert isinstance(data["distance_to_envelope_km"], (int, float)), "distance_to_envelope_km must be numeric"
        assert isinstance(data["range_km"], (int, float)), "range_km must be numeric"
        assert isinstance(data["azimuth_deg"], (int, float)), "azimuth_deg must be numeric"
    
    def test_infeasible_case_too_far(self, client):
        """Test infeasible case (too far) returns correct fields."""
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": 60.0, "lon": 30.0}  # ~8000 km away
        }
        
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["feasible"] == False, "Should be infeasible"
        assert "reasons" in data
        assert len(data["reasons"]) > 0
        # Should have a reason about range
        reasons_text = " ".join(data["reasons"])
        assert "too far" in reasons_text.lower() or "range" in reasons_text.lower()
    
    def test_infeasible_case_too_short(self, client):
        """Test infeasible case (too short) returns correct fields."""
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": 28.6, "lon": -80.5}  # Very close, ~10 km
        }
        
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["feasible"] == False, "Should be infeasible"
        assert "reasons" in data
        assert len(data["reasons"]) > 0


class TestTrajectoryEndpointUIContract:
    """Test /api/trajectory with exact UI payload format."""
    
    def test_feasible_trajectory_all_fields(self, client):
        """Test feasible trajectory returns all fields the UI expects.
        
        This is the exact payload format from static/app.js lines 283-285.
        UI expects trajectory points with: time_s, range_m, altitude_m, mach,
        latitude_deg, longitude_deg (lines 354, 359, 364, 617, 640, 666).
        """
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        
        response = client.post("/api/trajectory", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify feasibility fields (same as feasibility endpoint)
        assert "feasible" in data
        assert "reasons" in data
        assert "trajectory" in data
        
        # If feasible, verify trajectory structure
        if data["feasible"]:
            assert data["trajectory"] is not None, "trajectory should not be None for feasible case"
            assert len(data["trajectory"]) > 0, "trajectory should not be empty"
            
            # Check first trajectory point has all required fields
            point = data["trajectory"][0]
            required_fields = [
                "time_s",          # Used in altitudeTimeData (line 359)
                "range_m",         # Used in rangeData (line 354)
                "altitude_m",      # Used in both charts (lines 355, 360)
                "mach",            # Used in machTimeData (line 365)
                "latitude_deg",    # Used in 3D viz (line 618)
                "longitude_deg",   # Used in 3D viz (line 617)
            ]
            
            for field in required_fields:
                assert field in point, f"Trajectory point missing required field '{field}'"
                assert point[field] is not None, f"Field '{field}' should not be None"
                assert isinstance(point[field], (int, float)), f"Field '{field}' must be numeric"
            
            # Check last trajectory point (used for landing marker)
            last_point = data["trajectory"][-1]
            assert "latitude_deg" in last_point, "Last point must have latitude_deg"
            assert "longitude_deg" in last_point, "Last point must have longitude_deg"
        else:
            assert data["trajectory"] is None, "trajectory should be None for infeasible case"
    
    def test_infeasible_trajectory_no_data(self, client):
        """Test infeasible trajectory returns null trajectory."""
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": 60.0, "lon": 30.0}  # Too far
        }
        
        response = client.post("/api/trajectory", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["feasible"] == False
        assert data["trajectory"] is None, "Infeasible trajectory should return null trajectory"


class TestConfigEndpointUIContract:
    """Test /api/config GET and PUT with UI payload format."""
    
    def test_get_config_structure(self, client):
        """Test GET /api/config returns expected structure.
        
        UI expects: config object with nested structure (line 710-712).
        """
        response = client.get("/api/config")
        assert response.status_code == 200
        
        data = response.json()
        assert "config" in data, "Response must have 'config' field"
        
        config = data["config"]
        # Verify major sections exist
        expected_sections = ["vehicle", "aerodynamics", "limits", "environment", "sweep"]
        for section in expected_sections:
            assert section in config, f"Config missing section '{section}'"
    
    def test_put_config_validation(self, client):
        """Test PUT /api/config validates input."""
        # Get current config
        response = client.get("/api/config")
        current_config = response.json()["config"]
        
        # Valid config should be accepted
        response = client.put("/api/config", json=current_config)
        assert response.status_code == 200, "Valid config should be accepted"
        
        # Invalid config should be rejected
        invalid_config = {"invalid": "structure"}
        response = client.put("/api/config", json=invalid_config)
        assert response.status_code == 400, "Invalid config should return 400"


class TestCesiumTokenEndpointUIContract:
    """Test /api/cesium-token endpoint."""
    
    def test_cesium_token_structure(self, client):
        """Test GET /api/cesium-token returns expected structure.
        
        UI expects: token and has_token fields (lines 562-564).
        """
        response = client.get("/api/cesium-token")
        assert response.status_code == 200
        
        data = response.json()
        assert "token" in data, "Response must have 'token' field"
        assert "has_token" in data, "Response must have 'has_token' field"
        assert isinstance(data["has_token"], bool), "has_token must be boolean"


class TestInvalidInputValidation:
    """Test that invalid inputs are properly rejected with 422."""
    
    def test_latitude_out_of_bounds(self, client):
        """Test that invalid latitude is rejected."""
        # Latitude > 90
        payload = {
            "launch": {"lat": 95.0, "lon": -80.6},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 422, "Invalid latitude should return 422"
        
        # Latitude < -90
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": -95.0, "lon": -70.0}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 422, "Invalid latitude should return 422"
    
    def test_longitude_out_of_bounds(self, client):
        """Test that invalid longitude is rejected."""
        # Longitude > 180
        payload = {
            "launch": {"lat": 28.5, "lon": 185.0},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 422, "Invalid longitude should return 422"
        
        # Longitude < -180
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": 30.0, "lon": -185.0}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 422, "Invalid longitude should return 422"
    
    def test_missing_fields(self, client):
        """Test that missing required fields are rejected."""
        # Missing 'landing'
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 422, "Missing landing should return 422"
        
        # Missing 'lat' in launch
        payload = {
            "launch": {"lon": -80.6},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 422, "Missing lat should return 422"
    
    def test_wrong_types(self, client):
        """Test that wrong data types are rejected."""
        # String that can't be coerced to number
        payload = {
            "launch": {"lat": "invalid", "lon": -80.6},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 422, "Invalid type should return 422"
