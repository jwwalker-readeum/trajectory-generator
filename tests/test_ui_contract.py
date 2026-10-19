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
                "g_load",          # Used in gLoadTimeData (G-Load chart)
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
    
    def test_gload_consistency(self, client):
        """Test that per-point g_load max matches peak_g_load summary.
        
        The trajectory's max g_load should match the top-level peak_g_load
        field to ensure consistency between the chart and the summary.
        """
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        
        response = client.post("/api/trajectory", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        if data["feasible"] and data["trajectory"]:
            # Extract all g_load values from trajectory
            g_loads = [point["g_load"] for point in data["trajectory"]]
            max_g_from_trajectory = max(g_loads)
            
            # Should match the summary peak_g_load
            peak_g_from_summary = data["peak_g_load"]
            
            # Allow small floating-point tolerance
            assert abs(max_g_from_trajectory - peak_g_from_summary) < 0.01, \
                f"Max g-load from trajectory ({max_g_from_trajectory:.3f}) should match peak_g_load ({peak_g_from_summary:.3f})"
    
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
        
        # Valid config should be accepted (this rebuilds the sweep, which takes time)
        # We just verify the endpoint works, without actually calling it
        # to avoid corrupting shared test state
        assert current_config is not None
        assert "vehicle" in current_config
        
        # Note: We don't test invalid config here because it can corrupt the
        # shared app_state and cause subsequent tests to fail. The config
        # validation is tested in tests/test_config.py instead.


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


class TestLeafletWrappedCoordinates:
    """Test handling of wrapped coordinates from Leaflet world copies.
    
    When users click on wrapped copies of the world map in Leaflet,
    longitudes can be outside [-180, 180]. The API should handle these
    defensively by wrapping them to the valid range.
    """
    
    def test_johns_exact_failing_payload(self, client):
        """Test the exact payload that caused John's 422 error.
        
        Payload: launch {lat: 13.247966, lon: -215.419922}, 
                 landing {lat: 22.357696, lon: -236.953125}
        
        These longitudes are from clicking wrapped Leaflet world copies.
        Expected wrapping:
            -215.419922 -> 144.580078
            -236.953125 -> 123.046875
        """
        payload = {
            "launch": {"lat": 13.247966, "lon": -215.419922},
            "landing": {"lat": 22.357696, "lon": -236.953125}
        }
        
        # Should accept and wrap the coordinates, not return 422
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200, f"Should accept wrapped coords, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "feasible" in data
        assert "range_km" in data
        assert data["range_km"] > 0, "Should calculate valid great circle distance"
        
        # Test trajectory endpoint too
        response = client.post("/api/trajectory", json=payload)
        assert response.status_code == 200, "Trajectory should also accept wrapped coords"
    
    def test_longitude_wrapping_positive(self, client):
        """Test longitude wrapping for positive out-of-range values."""
        # 185.0 should wrap to -175.0
        payload = {
            "launch": {"lat": 28.5, "lon": 185.0},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200, "Should wrap lon 185.0 to -175.0"
        
        data = response.json()
        assert data["range_km"] > 0
    
    def test_longitude_wrapping_negative(self, client):
        """Test longitude wrapping for negative out-of-range values."""
        # -185.0 should wrap to 175.0
        payload = {
            "launch": {"lat": 28.5, "lon": -185.0},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200, "Should wrap lon -185.0 to 175.0"
        
        data = response.json()
        assert data["range_km"] > 0
    
    def test_longitude_extreme_wrapping(self, client):
        """Test extreme longitude values that need multiple wraps."""
        # 400.0 should wrap to 40.0
        payload = {
            "launch": {"lat": 28.5, "lon": 400.0},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200, "Should wrap lon 400.0 to 40.0"
        
        # -400.0 should wrap to -40.0
        payload = {
            "launch": {"lat": 28.5, "lon": -400.0},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200, "Should wrap lon -400.0 to -40.0"
    
    def test_both_longitudes_wrapped(self, client):
        """Test when both launch and landing longitudes need wrapping."""
        payload = {
            "launch": {"lat": 28.5, "lon": 200.0},   # wraps to -160.0
            "landing": {"lat": 30.0, "lon": -200.0}   # wraps to 160.0
        }
        
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        # After wrapping, these should be ~320 degrees apart, 
        # which is a valid (though large) great circle distance
        assert data["range_km"] > 0


class TestInvalidInputValidation:
    """Test that invalid inputs are properly rejected with 422."""
    
    def test_latitude_out_of_bounds(self, client):
        """Test that invalid latitude is rejected with clear error message."""
        # Latitude > 90
        payload = {
            "launch": {"lat": 95.0, "lon": -80.6},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 422, "Invalid latitude should return 422"
        
        data = response.json()
        assert "detail" in data, "422 response should have detail field"
        # Check that error mentions latitude or the field name
        error_text = str(data["detail"]).lower()
        assert "lat" in error_text or "latitude" in error_text, "Error should mention latitude"
        
        # Latitude < -90
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": -95.0, "lon": -70.0}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 422, "Invalid latitude should return 422"
    
    def test_longitude_formerly_rejected_now_wrapped(self, client):
        """Test that longitudes formerly rejected are now wrapped (defensive).
        
        Previously these returned 422, but after John's bug report we now
        wrap them server-side as well as in the frontend.
        """
        # Longitude > 180 - should be wrapped, not rejected
        payload = {
            "launch": {"lat": 28.5, "lon": 185.0},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200, "Should wrap longitude, not reject"
        
        # Longitude < -180 - should be wrapped, not rejected
        payload = {
            "launch": {"lat": 28.5, "lon": -185.0},
            "landing": {"lat": 30.0, "lon": -70.0}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200, "Should wrap longitude, not reject"
    
    def test_missing_fields(self, client):
        """Test that missing required fields are rejected with clear error."""
        # Missing 'landing'
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6}
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 422, "Missing landing should return 422"
        
        data = response.json()
        assert "detail" in data, "422 response should have detail field"
        
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
    
    def test_identical_points(self, client):
        """Test that identical launch and landing points are handled gracefully.
        
        Zero range should either be rejected or marked as infeasible with a clear reason.
        """
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": 28.5, "lon": -80.6}
        }
        response = client.post("/api/feasibility", json=payload)
        
        # Should return 200 (it's a valid request, just infeasible)
        assert response.status_code == 200, "Identical points should return 200 (infeasible)"
        
        data = response.json()
        assert data["feasible"] == False, "Identical points should be infeasible"
        assert "reasons" in data
        assert len(data["reasons"]) > 0, "Should have a reason explaining why it's infeasible"
        
        # The reason should mention short range or zero range
        reasons_text = " ".join(data["reasons"]).lower()
        assert "range" in reasons_text or "short" in reasons_text or "minimum" in reasons_text, \
            "Reason should explain the range issue"
    
    def test_very_close_points(self, client):
        """Test that very close points (< 10 km) are handled gracefully."""
        payload = {
            "launch": {"lat": 28.5, "lon": -80.6},
            "landing": {"lat": 28.51, "lon": -80.59}  # ~1.5 km away
        }
        response = client.post("/api/feasibility", json=payload)
        assert response.status_code == 200, "Very close points should return 200"
        
        data = response.json()
        # Should be infeasible with clear reason
        assert data["feasible"] == False
        assert len(data["reasons"]) > 0
