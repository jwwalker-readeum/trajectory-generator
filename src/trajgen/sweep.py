"""Offline sweep to build reachability envelope.

NOTIONAL DEMO RESULTS - All sweep data is for demonstration only.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

from .config import VehicleConfig
from .simulation import TrajectorySimulation


@dataclass
class SweepPoint:
    """Single point in parameter sweep."""
    launch_angle_deg: float
    burn_param: float
    range_km: float
    peak_g_load: float
    peak_heat_flux_w_cm2: float
    feasible: bool
    reasons: List[str]


class ReachabilitySweep:
    """Build and cache reachability envelope."""
    
    def __init__(self, config: VehicleConfig, cache_dir: Path = None):
        """Initialize sweep manager.
        
        Args:
            config: Vehicle configuration
            cache_dir: Directory for cache files (default: .cache in repo root)
        """
        self.config = config
        self.simulation = TrajectorySimulation(config)
        
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / '.cache'
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.cache_file = self.cache_dir / 'sweep_cache.json'
        self.sweep_data: List[SweepPoint] = []
    
    def load_or_build(self) -> None:
        """Load sweep from cache or build if needed."""
        # Check if cache exists and is valid
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                
                # Validate cache
                if cache.get('config_hash') == self.config.config_hash:
                    print(f"Loading sweep cache with {len(cache['data'])} points")
                    self.sweep_data = [
                        SweepPoint(**point) for point in cache['data']
                    ]
                    return
                else:
                    print("Config changed, rebuilding sweep")
            except Exception as e:
                print(f"Cache load failed: {e}, rebuilding")
        
        # Build new sweep
        self.build()
    
    def build(self) -> None:
        """Build reachability sweep."""
        print("Building reachability sweep...")
        
        vehicle = self.config['vehicle']
        sweep_config = self.config['sweep']
        limits = self.config['limits']
        
        angle_min, angle_max = vehicle['launch']['angle_range_deg']
        angle_step = sweep_config['launch_angle_step_deg']
        burn_param_step = sweep_config['burn_param_step']
        
        angles = np.arange(angle_min, angle_max + angle_step, angle_step)
        burn_params = np.arange(0.5, 1.0 + burn_param_step, burn_param_step)
        
        sweep_data = []
        total_points = len(angles) * len(burn_params)
        completed = 0
        
        # Use nominal launch point for sweep
        launch_lat, launch_lon = 28.5, -80.6  # Cape Canaveral
        azimuth = 90.0  # East
        
        for angle in angles:
            for burn_param in burn_params:
                success, trajectory, error = self.simulation.simulate(
                    launch_angle_deg=float(angle),
                    burn_param=float(burn_param),
                    launch_lat=launch_lat,
                    launch_lon=launch_lon,
                    azimuth_deg=azimuth
                )
                
                if success and len(trajectory) > 0:
                    final_point = trajectory[-1]
                    range_km = final_point.range_m / 1000.0
                    
                    peaks = self.simulation.get_peak_values(trajectory)
                    peak_g = peaks['peak_g_load']
                    peak_heat = peaks['peak_heat_flux_w_cm2']
                    
                    # Check feasibility
                    feasible = True
                    reasons = []
                    
                    if peak_g > limits['max_g_load']:
                        feasible = False
                        reasons.append(f"g-load exceeds limit ({peak_g:.1f} > {limits['max_g_load']})")
                    
                    if peak_heat > limits['max_stagnation_heat_flux_w_cm2']:
                        feasible = False
                        reasons.append(f"heat flux exceeds limit ({peak_heat:.1f} > {limits['max_stagnation_heat_flux_w_cm2']})")
                    
                    sweep_data.append(SweepPoint(
                        launch_angle_deg=float(angle),
                        burn_param=float(burn_param),
                        range_km=range_km,
                        peak_g_load=peak_g,
                        peak_heat_flux_w_cm2=peak_heat,
                        feasible=feasible,
                        reasons=reasons
                    ))
                
                completed += 1
                if completed % 50 == 0:
                    print(f"  Progress: {completed}/{total_points} ({100*completed/total_points:.1f}%)")
        
        self.sweep_data = sweep_data
        print(f"Sweep complete: {len(sweep_data)} valid points")
        
        # Save cache
        self.save_cache()
    
    def save_cache(self) -> None:
        """Save sweep to cache."""
        cache = {
            'config_hash': self.config.config_hash,
            'data': [asdict(point) for point in self.sweep_data]
        }
        
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f)
        
        print(f"Sweep cached to {self.cache_file}")
    
    def rebuild(self) -> None:
        """Force rebuild of sweep."""
        if self.cache_file.exists():
            self.cache_file.unlink()
        self.build()
    
    def get_range_bounds(self) -> Tuple[float, float]:
        """Get minimum and maximum feasible ranges.
        
        Returns:
            (min_range_km, max_range_km)
        """
        feasible_points = [p for p in self.sweep_data if p.feasible]
        if not feasible_points:
            return 0, 0
        
        ranges = [p.range_km for p in feasible_points]
        return min(ranges), max(ranges)
    
    def find_nearest_parameters(
        self,
        target_range_km: float
    ) -> Tuple[float, float, float]:
        """Find sweep parameters nearest to target range.
        
        Args:
            target_range_km: Desired range in km
            
        Returns:
            (launch_angle_deg, burn_param, achieved_range_km)
        """
        if not self.sweep_data:
            return 45.0, 1.0, 0.0
        
        # Find closest point
        best_point = min(
            self.sweep_data,
            key=lambda p: abs(p.range_km - target_range_km)
        )
        
        return best_point.launch_angle_deg, best_point.burn_param, best_point.range_km
    
    def get_feasible_ranges(self) -> List[float]:
        """Get list of all feasible ranges.
        
        Returns:
            List of feasible ranges in km
        """
        return [p.range_km for p in self.sweep_data if p.feasible]
