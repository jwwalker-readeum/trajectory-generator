"""Tests for configuration loading and validation."""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.trajgen.config import VehicleConfig, ConfigError


def test_load_default_config():
    """Test loading default config from repo root."""
    config = VehicleConfig()
    assert config['vehicle']['name'] == 'demo-vehicle-v0'
    assert len(config['vehicle']['stages']) == 2
    assert config['environment']['atmosphere'] == 'us_standard_1976'


def test_config_validation():
    """Test configuration validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        # Invalid config - missing required keys
        yaml.dump({'vehicle': {}}, f)
        f.flush()
        temp_path = f.name
    
    try:
        with pytest.raises(ConfigError):
            VehicleConfig(temp_path)
    finally:
        Path(temp_path).unlink()


def test_config_stages_validation():
    """Test stage configuration validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config_data = {
            'vehicle': {
                'stages': [{'name': 'stage1'}]  # Only one stage, need 2
            },
            'aerodynamics': {
                'reference_area_m2': 0.3,
                'cd_vs_mach': [[0, 0.3], [1, 0.5]],
                'reentry_ballistic_coeff_kg_m2': 4000,
                'nose_radius_m': 0.05
            },
            'limits': {'max_g_load': 40, 'max_stagnation_heat_flux_w_cm2': 1500},
            'environment': {'atmosphere': 'us_standard_1976'},
            'sweep': {'launch_angle_step_deg': 1, 'burn_param_step': 0.05}
        }
        yaml.dump(config_data, f)
        f.flush()
        temp_path = f.name
    
    try:
        with pytest.raises(ConfigError, match="exactly 2 stages"):
            VehicleConfig(temp_path)
    finally:
        Path(temp_path).unlink()


def test_config_hash():
    """Test config hash generation for cache invalidation."""
    config = VehicleConfig()
    hash1 = config.config_hash
    assert len(hash1) == 64  # SHA256 hex digest
    
    # Reload should give same hash
    config.load()
    hash2 = config.config_hash
    assert hash1 == hash2


def test_config_get():
    """Test config value retrieval."""
    config = VehicleConfig()
    
    # Test dict-like access
    assert config['vehicle']['name'] == 'demo-vehicle-v0'
    
    # Test get method
    assert config.get('vehicle') is not None
    assert config.get('nonexistent', 'default') == 'default'


def test_config_to_dict():
    """Test config conversion to dictionary."""
    config = VehicleConfig()
    config_dict = config.to_dict()
    
    assert isinstance(config_dict, dict)
    assert 'vehicle' in config_dict
    assert 'aerodynamics' in config_dict
