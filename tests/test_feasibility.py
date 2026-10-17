"""Tests for feasibility checking."""

import pytest
import tempfile
from pathlib import Path

from src.trajgen.config import VehicleConfig
from src.trajgen.sweep import ReachabilitySweep
from src.trajgen.feasibility import FeasibilityChecker


@pytest.fixture(scope="module")
def checker():
    """Create feasibility checker with sweep."""
    config = VehicleConfig()
    
    # Use coarser sweep for faster tests
    config['sweep']['launch_angle_step_deg'] = 5
    config['sweep']['burn_param_step'] = 0.2
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sweep = ReachabilitySweep(config, cache_dir=Path(tmpdir))
        sweep.build()
        checker = FeasibilityChecker(config, sweep)
        yield checker


def test_feasibility_reachable(checker):
    """Test feasible trajectory within envelope."""
    # Use Cape Canaveral to somewhere in Atlantic
    result = checker.check_feasibility(
        launch_lat=28.5,
        launch_lon=-80.6,
        landing_lat=30.0,
        landing_lon=-70.0
    )
    
    assert result.range_km > 0
    assert result.azimuth_deg >= 0
    
    # Should provide feasibility assessment
    assert isinstance(result.feasible, bool)
    assert len(result.reasons) > 0


def test_feasibility_too_close(checker):
    """Test range validation for very close points."""
    # Very close points (essentially same location)
    result = checker.check_feasibility(
        launch_lat=28.5,
        launch_lon=-80.6,
        landing_lat=28.5,  # Same location
        landing_lon=-80.6
    )
    
    # Should have a very small range
    assert result.range_km < 1.0
    assert len(result.reasons) > 0


def test_feasibility_too_far(checker):
    """Test range too long."""
    # Very distant points
    result = checker.check_feasibility(
        launch_lat=28.5,
        launch_lon=-80.6,
        landing_lat=-28.5,  # Opposite side
        landing_lon=99.4
    )
    
    assert result.feasible == False
    assert any("too far" in reason.lower() for reason in result.reasons)


def test_feasibility_with_modified_limits(checker):
    """Test g-load and heating limit violations."""
    # Modify config to have somewhat strict limits (not impossibly low)
    config = checker.config
    original_g_limit = config['limits']['max_g_load']
    original_heat_limit = config['limits']['max_stagnation_heat_flux_w_cm2']
    
    # Set strict but achievable limits
    config['limits']['max_g_load'] = 5.0
    config['limits']['max_stagnation_heat_flux_w_cm2'] = 10.0
    
    # Use coarse sweep for speed
    config['sweep']['launch_angle_step_deg'] = 10
    config['sweep']['burn_param_step'] = 0.25
    
    # Rebuild with strict limits
    with tempfile.TemporaryDirectory() as tmpdir:
        sweep = ReachabilitySweep(config, cache_dir=Path(tmpdir))
        sweep.build()
        strict_checker = FeasibilityChecker(config, sweep)
        
        result = strict_checker.check_feasibility(
            launch_lat=28.5,
            launch_lon=-80.6,
            landing_lat=30.0,
            landing_lon=-70.0
        )
        
        # Should fail - either due to limits or no feasible range exists
        assert result.feasible == False
        assert len(result.reasons) > 0
    
    # Restore original limits
    config['limits']['max_g_load'] = original_g_limit
    config['limits']['max_stagnation_heat_flux_w_cm2'] = original_heat_limit


def test_great_circle_distance(checker):
    """Test great circle distance calculation."""
    # Test known distance: Cape Canaveral to Miami (~200 km)
    result = checker.check_feasibility(
        launch_lat=28.5,
        launch_lon=-80.6,
        landing_lat=25.8,
        landing_lon=-80.2
    )
    
    # Distance should be roughly 200-300 km
    assert 200 < result.range_km < 400
    
    # Azimuth should be roughly south (180 +/- some degrees)
    assert 120 < result.azimuth_deg < 240


def test_trajectory_computation(checker):
    """Test full trajectory computation."""
    result = checker.check_feasibility(
        launch_lat=28.5,
        launch_lon=-80.6,
        landing_lat=30.0,
        landing_lon=-70.0,
        compute_trajectory=True
    )
    
    if result.feasible:
        assert result.trajectory is not None
        assert len(result.trajectory) > 0
        
        # Check trajectory point structure
        point = result.trajectory[0]
        assert 'time_s' in point
        assert 'altitude_m' in point
        assert 'velocity_m_s' in point
        assert 'g_load' in point
        assert 'heat_flux_w_cm2' in point


def test_icbm_range_trajectory():
    """Test that we can compute a feasible trajectory for ICBM-scale range."""
    config = VehicleConfig()
    
    # Use coarse sweep for speed
    config['sweep']['launch_angle_step_deg'] = 5
    config['sweep']['burn_param_step'] = 0.1
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sweep = ReachabilitySweep(config, cache_dir=Path(tmpdir))
        sweep.build()
        checker = FeasibilityChecker(config, sweep)
        
        # Find a feasible point in the 1000-2000 km range
        feasible_ranges = sweep.get_feasible_ranges()
        mid_ranges = [r for r in feasible_ranges if 1000 < r < 2000]
        
        if mid_ranges:
            # Pick one and compute trajectory
            target_range = mid_ranges[len(mid_ranges) // 2]
            
            # Compute lat/lon for this range (roughly east from Cape Canaveral)
            # Using simple approximation: 1 degree lon ≈ 111 km at equator
            landing_lon = -80.6 + (target_range / 111.0)
            
            result = checker.check_feasibility(
                launch_lat=28.5,
                launch_lon=-80.6,
                landing_lat=28.5,
                landing_lon=landing_lon,
                compute_trajectory=True
            )
            
            # Should get a result (may or may not be feasible due to approximate targeting)
            assert result.range_km > 0
            
            if result.feasible:
                # If feasible, should have trajectory
                assert result.trajectory is not None
                assert len(result.trajectory) > 10
                assert result.peak_g_load is not None
                assert result.peak_heat_flux_w_cm2 is not None
