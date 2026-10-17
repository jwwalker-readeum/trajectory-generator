"""Configuration loader and validator for vehicle parameters.

All values are NOTIONAL DEMO PLACEHOLDERS only.
"""

import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List


class ConfigError(Exception):
    """Configuration validation error."""
    pass


class VehicleConfig:
    """Vehicle configuration with validation and reloading support."""
    
    def __init__(self, config_path: str | None = None):
        """Initialize config loader.
        
        Args:
            config_path: Path to config file. If None, uses VEHICLE_CONFIG_PATH env var
                        or defaults to vehicle_config.yaml in repo root.
        """
        if config_path is None:
            config_path = os.environ.get(
                'VEHICLE_CONFIG_PATH',
                str(Path(__file__).parent.parent.parent / 'vehicle_config.yaml')
            )
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._config_hash: str = ""
        self.load()
    
    def load(self) -> None:
        """Load and validate configuration from file."""
        if not self.config_path.exists():
            raise ConfigError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            content = f.read()
            self._config = yaml.safe_load(content)
            self._config_hash = hashlib.sha256(content.encode()).hexdigest()
        
        self._validate()
    
    def save(self, config_dict: Dict[str, Any]) -> None:
        """Save and reload configuration.
        
        Args:
            config_dict: New configuration dictionary
        """
        # Validate before saving
        self._config = config_dict
        self._validate()
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
        
        self.load()
    
    def _validate(self) -> None:
        """Validate configuration structure and values."""
        required_keys = ['vehicle', 'aerodynamics', 'limits', 'environment', 'sweep']
        for key in required_keys:
            if key not in self._config:
                raise ConfigError(f"Missing required top-level key: {key}")
        
        # Validate vehicle
        vehicle = self._config['vehicle']
        if 'stages' not in vehicle or len(vehicle['stages']) != 2:
            raise ConfigError("Vehicle must have exactly 2 stages")
        
        for i, stage in enumerate(vehicle['stages']):
            required_stage_keys = ['name', 'mass_launch_kg', 'mass_burnout_kg', 
                                  'thrust_n', 'isp_s', 'burn_time_s']
            for key in required_stage_keys:
                if key not in stage:
                    raise ConfigError(f"Stage {i} missing required key: {key}")
                if not isinstance(stage[key], (int, float, str)):
                    raise ConfigError(f"Stage {i} key {key} has invalid type")
            
            if stage['mass_burnout_kg'] >= stage['mass_launch_kg']:
                raise ConfigError(f"Stage {i} burnout mass must be less than launch mass")
        
        # Validate reentry vehicle
        if 'reentry_vehicle' not in vehicle:
            raise ConfigError("Missing reentry_vehicle configuration")
        rv = vehicle['reentry_vehicle']
        if 'mass_kg' not in rv or 'separates_after' not in rv:
            raise ConfigError("Reentry vehicle missing required keys")
        
        # Validate aerodynamics
        aero = self._config['aerodynamics']
        required_aero = ['reference_area_m2', 'cd_vs_mach', 'reentry_ballistic_coeff_kg_m2', 'nose_radius_m']
        for key in required_aero:
            if key not in aero:
                raise ConfigError(f"Aerodynamics missing required key: {key}")
        
        if not isinstance(aero['cd_vs_mach'], list) or len(aero['cd_vs_mach']) < 2:
            raise ConfigError("cd_vs_mach must be a list with at least 2 points")
        
        # Validate limits
        limits = self._config['limits']
        if 'max_g_load' not in limits or 'max_stagnation_heat_flux_w_cm2' not in limits:
            raise ConfigError("Limits missing required keys")
        
        # Validate environment
        env = self._config['environment']
        if env.get('atmosphere') != 'us_standard_1976':
            raise ConfigError("Only us_standard_1976 atmosphere is supported")
        
        # Validate sweep
        sweep = self._config['sweep']
        if 'launch_angle_step_deg' not in sweep or 'burn_param_step' not in sweep:
            raise ConfigError("Sweep missing required keys")
    
    @property
    def config_hash(self) -> str:
        """Get hash of current configuration for cache invalidation."""
        return self._config_hash
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self._config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Get configuration value by key."""
        return self._config[key]
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()
