"""Tests for reachability sweep."""

import pytest
import tempfile
from pathlib import Path

from src.trajgen.config import VehicleConfig
from src.trajgen.sweep import ReachabilitySweep


def test_sweep_initialization():
    """Test sweep initialization."""
    config = VehicleConfig()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sweep = ReachabilitySweep(config, cache_dir=Path(tmpdir))
        assert sweep.config is not None
        assert sweep.cache_dir.exists()


def test_sweep_build():
    """Test sweep building with coarse parameters for speed."""
    config = VehicleConfig()
    
    # Use coarser sweep for faster testing
    config['sweep']['launch_angle_step_deg'] = 10
    config['sweep']['burn_param_step'] = 0.25
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sweep = ReachabilitySweep(config, cache_dir=Path(tmpdir))
        sweep.build()
        
        assert len(sweep.sweep_data) > 0
        
        # Check sweep point structure
        point = sweep.sweep_data[0]
        assert hasattr(point, 'launch_angle_deg')
        assert hasattr(point, 'burn_param')
        assert hasattr(point, 'range_km')
        assert hasattr(point, 'peak_g_load')
        assert hasattr(point, 'peak_heat_flux_w_cm2')
        assert hasattr(point, 'feasible')
        assert hasattr(point, 'reasons')


def test_sweep_cache():
    """Test sweep caching."""
    config = VehicleConfig()
    
    # Use coarser sweep for faster testing
    config['sweep']['launch_angle_step_deg'] = 10
    config['sweep']['burn_param_step'] = 0.25
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        
        # Build and cache
        sweep1 = ReachabilitySweep(config, cache_dir=cache_dir)
        sweep1.build()
        
        cache_file = cache_dir / 'sweep_cache.json'
        assert cache_file.exists()
        
        # Load from cache
        sweep2 = ReachabilitySweep(config, cache_dir=cache_dir)
        sweep2.load_or_build()
        
        # Should have same number of points
        assert len(sweep2.sweep_data) == len(sweep1.sweep_data)


def test_range_bounds():
    """Test range bounds extraction."""
    config = VehicleConfig()
    
    # Use coarser sweep for faster testing
    config['sweep']['launch_angle_step_deg'] = 10
    config['sweep']['burn_param_step'] = 0.25
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sweep = ReachabilitySweep(config, cache_dir=Path(tmpdir))
        sweep.build()
        
        min_range, max_range = sweep.get_range_bounds()
        
        assert min_range > 0
        assert max_range > min_range
        assert min_range < 10000  # Should be less than 10,000 km
        assert max_range < 10000


def test_find_nearest_parameters():
    """Test finding nearest parameters for target range."""
    config = VehicleConfig()
    
    # Use coarser sweep for faster testing
    config['sweep']['launch_angle_step_deg'] = 10
    config['sweep']['burn_param_step'] = 0.25
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sweep = ReachabilitySweep(config, cache_dir=Path(tmpdir))
        sweep.build()
        
        # Find parameters for mid-range target
        min_range, max_range = sweep.get_range_bounds()
        
        if max_range > min_range:
            target_range = (min_range + max_range) / 2
            
            angle, burn_param, achieved_range = sweep.find_nearest_parameters(target_range)
            
            # With coarse sweep, angle might slightly exceed nominal range due to arange behavior
            assert 20 <= angle <= 95  # Allow some tolerance
            assert 0.5 <= burn_param <= 1.0
            assert achieved_range >= 0


def test_default_envelope_is_icbm_scale():
    """Test that default config produces ICBM-scale ranges (target ~2500-2900 km)."""
    config = VehicleConfig()
    
    # Use coarser sweep for faster testing
    config['sweep']['launch_angle_step_deg'] = 5
    config['sweep']['burn_param_step'] = 0.1
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sweep = ReachabilitySweep(config, cache_dir=Path(tmpdir))
        sweep.build()
        
        min_range, max_range = sweep.get_range_bounds()
        
        # Assert we have a non-trivial envelope
        assert max_range > 100, f"Max range {max_range:.1f} km is too small for useful demo"
        
        # Assert envelope reaches ICBM-scale ranges
        assert max_range > 2000, f"Max range {max_range:.1f} km should reach ICBM scale (~2500+ km)"
        
        # Verify we have feasible points in the mid-range
        feasible_ranges = sweep.get_feasible_ranges()
        assert len(feasible_ranges) > 5, "Should have multiple feasible trajectories"
        
        mid_range_points = [r for r in feasible_ranges if 1000 < r < 2500]
        assert len(mid_range_points) > 0, "Should have feasible points in mid-range (1000-2500 km)"
