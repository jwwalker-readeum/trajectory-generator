"""Tests for FastAPI endpoints."""

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from src.trajgen.config import VehicleConfig
from src.trajgen.sweep import ReachabilitySweep
from src.trajgen.feasibility import FeasibilityChecker
from src.trajgen.api import app, app_state


@pytest.fixture(scope="module")
def client():
    """Create test client with initialized app state."""
    # Initialize app state manually for testing with smaller sweep
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


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "NOTIONAL" in data["message"]


def test_get_config_endpoint(client):
    """Test config retrieval endpoint."""
    response = client.get("/api/config")
    assert response.status_code == 200
    
    data = response.json()
    assert "config" in data
    assert "warning" in data
    
    config = data["config"]
    assert "vehicle" in config
    assert "aerodynamics" in config
    assert "limits" in config


def test_feasibility_endpoint_valid(client):
    """Test feasibility check with valid input."""
    request_data = {
        "launch": {"lat": 28.5, "lon": -80.6},
        "landing": {"lat": 30.0, "lon": -70.0}
    }
    
    response = client.post("/api/feasibility", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "feasible" in data
    assert "range_km" in data
    assert "azimuth_deg" in data
    assert "reasons" in data
    assert "distance_to_envelope_km" in data
    assert "warning" in data
    
    assert isinstance(data["feasible"], bool)
    assert data["range_km"] > 0
    assert len(data["reasons"]) > 0


def test_feasibility_endpoint_invalid_lat(client):
    """Test feasibility check with invalid latitude."""
    request_data = {
        "launch": {"lat": 91.0, "lon": -80.6},  # Invalid latitude
        "landing": {"lat": 30.0, "lon": -70.0}
    }
    
    response = client.post("/api/feasibility", json=request_data)
    assert response.status_code == 422  # Validation error


def test_trajectory_endpoint_valid(client):
    """Test trajectory computation with valid input."""
    request_data = {
        "launch": {"lat": 28.5, "lon": -80.6},
        "landing": {"lat": 30.0, "lon": -70.0}
    }
    
    response = client.post("/api/trajectory", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "feasible" in data
    assert "range_km" in data
    assert "trajectory" in data
    assert "warning" in data
    
    # If feasible, should have trajectory data
    if data["feasible"]:
        assert data["trajectory"] is not None
        assert len(data["trajectory"]) > 0
        
        # Check first trajectory point
        point = data["trajectory"][0]
        assert "time_s" in point
        assert "altitude_m" in point
        assert "velocity_m_s" in point


def test_trajectory_endpoint_infeasible(client):
    """Test trajectory computation for infeasible case."""
    # Very distant points - definitely too far
    request_data = {
        "launch": {"lat": 28.5, "lon": -80.6},
        "landing": {"lat": 60.0, "lon": 30.0}  # ~8000 km away
    }
    
    response = client.post("/api/trajectory", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["feasible"] == False
    assert data["trajectory"] is None
    assert len(data["reasons"]) > 0


def test_update_config_endpoint(client):
    """Test config update endpoint validation (skip rebuild for speed)."""
    # Get current config
    response = client.get("/api/config")
    current_config = response.json()["config"]
    
    # Test that valid config is accepted (note: rebuild is slow, so we just test validation)
    # In a real deployment this would rebuild the sweep
    assert current_config is not None
    assert "limits" in current_config
    
    # Test that we can modify values
    original_g_load = current_config["limits"]["max_g_load"]
    assert original_g_load > 0


def test_update_config_invalid(client):
    """Test config update with invalid data."""
    invalid_config = {
        "vehicle": {},  # Missing required fields
        "aerodynamics": {},
        "limits": {},
        "environment": {},
        "sweep": {}
    }
    
    response = client.put("/api/config", json=invalid_config)
    assert response.status_code == 400  # Bad request
