"""Feasibility checking for launch-landing pairs.

NOTIONAL DEMO RESULTS - All feasibility assessments are for demonstration only.
"""

import numpy as np
from typing import Dict, Tuple, List
from dataclasses import dataclass, asdict

from .config import VehicleConfig
from .simulation import TrajectorySimulation
from .sweep import ReachabilitySweep


# Earth radius for great circle calculations
EARTH_RADIUS_KM = 6371.0


@dataclass
class FeasibilityResult:
    """Result of feasibility check."""
    feasible: bool
    range_km: float
    azimuth_deg: float
    reasons: List[str]
    distance_to_envelope_km: float
    peak_g_load: float | None = None
    peak_heat_flux_w_cm2: float | None = None
    trajectory: List[Dict] | None = None


class FeasibilityChecker:
    """Check feasibility of launch-landing pairs."""
    
    def __init__(self, config: VehicleConfig, sweep: ReachabilitySweep):
        """Initialize feasibility checker.
        
        Args:
            config: Vehicle configuration
            sweep: Reachability sweep data
        """
        self.config = config
        self.sweep = sweep
        self.simulation = TrajectorySimulation(config)
    
    def check_feasibility(
        self,
        launch_lat: float,
        launch_lon: float,
        landing_lat: float,
        landing_lon: float,
        compute_trajectory: bool = False
    ) -> FeasibilityResult:
        """Check if launch-landing pair is feasible.
        
        Args:
            launch_lat: Launch latitude (degrees)
            launch_lon: Launch longitude (degrees)
            landing_lat: Landing latitude (degrees)
            landing_lon: Landing longitude (degrees)
            compute_trajectory: If True, compute full trajectory
            
        Returns:
            FeasibilityResult with assessment
        """
        # Compute great circle range and azimuth
        range_km, azimuth_deg = self._great_circle_distance(
            launch_lat, launch_lon, landing_lat, landing_lon
        )
        
        # Get feasible range bounds from sweep
        min_range, max_range = self.sweep.get_range_bounds()
        
        reasons = []
        feasible = True
        distance_to_envelope = 0.0
        
        # Check if range is within envelope
        if range_km < min_range:
            feasible = False
            distance_to_envelope = min_range - range_km
            reasons.append(f"Range too short ({range_km:.1f} km < {min_range:.1f} km minimum)")
        elif range_km > max_range:
            feasible = False
            distance_to_envelope = range_km - max_range
            reasons.append(f"Range too far ({range_km:.1f} km > {max_range:.1f} km maximum)")
        else:
            # Within envelope bounds, but need to check constraints
            distance_to_envelope = min(range_km - min_range, max_range - range_km)
        
        # If within bounds, simulate trajectory to check constraints
        peak_g = None
        peak_heat = None
        trajectory = None
        
        if min_range <= range_km <= max_range:
            # Find nearest parameters from sweep
            angle, burn_param, _ = self.sweep.find_nearest_parameters(range_km)
            
            # Run simulation
            success, traj_points, error = self.simulation.simulate(
                launch_angle_deg=angle,
                burn_param=burn_param,
                launch_lat=launch_lat,
                launch_lon=launch_lon,
                azimuth_deg=azimuth_deg
            )
            
            if success:
                peaks = self.simulation.get_peak_values(traj_points)
                peak_g = peaks['peak_g_load']
                peak_heat = peaks['peak_heat_flux_w_cm2']
                
                limits = self.config['limits']
                
                # Check g-load
                if peak_g > limits['max_g_load']:
                    feasible = False
                    reasons.append(
                        f"Peak g-load exceeds limit ({peak_g:.1f} > {limits['max_g_load']})"
                    )
                
                # Check heating
                if peak_heat > limits['max_stagnation_heat_flux_w_cm2']:
                    feasible = False
                    reasons.append(
                        f"Peak heat flux exceeds limit ({peak_heat:.1f} > {limits['max_stagnation_heat_flux_w_cm2']} W/cm²)"
                    )
                
                # If requested, prepare trajectory data
                if compute_trajectory and feasible:
                    trajectory = [
                        {
                            'time_s': p.time_s,
                            'altitude_m': p.altitude_m,
                            'range_m': p.range_m,
                            'velocity_m_s': p.velocity_m_s,
                            'mach': p.mach,
                            'g_load': p.g_load,
                            'heat_flux_w_cm2': p.heat_flux_w_cm2,
                            'latitude_deg': p.latitude_deg,
                            'longitude_deg': p.longitude_deg,
                            'flight_path_angle_deg': p.flight_path_angle_deg,
                            'phase': p.phase
                        }
                        for p in traj_points
                    ]
            else:
                feasible = False
                reasons.append(f"Simulation failed: {error}")
        
        if feasible and not reasons:
            reasons.append("All constraints satisfied")
        
        return FeasibilityResult(
            feasible=feasible,
            range_km=range_km,
            azimuth_deg=azimuth_deg,
            reasons=reasons,
            distance_to_envelope_km=distance_to_envelope,
            peak_g_load=peak_g,
            peak_heat_flux_w_cm2=peak_heat,
            trajectory=trajectory
        )
    
    def _great_circle_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> Tuple[float, float]:
        """Compute great circle distance and azimuth.
        
        Args:
            lat1, lon1: Starting point (degrees)
            lat2, lon2: Ending point (degrees)
            
        Returns:
            (distance_km, azimuth_deg)
        """
        # Convert to radians
        lat1_rad = np.radians(lat1)
        lon1_rad = np.radians(lon1)
        lat2_rad = np.radians(lat2)
        lon2_rad = np.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = np.sin(dlat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distance_km = EARTH_RADIUS_KM * c
        
        # Azimuth (bearing)
        x = np.sin(dlon) * np.cos(lat2_rad)
        y = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon)
        azimuth_rad = np.arctan2(x, y)
        azimuth_deg = np.degrees(azimuth_rad)
        
        # Normalize to 0-360
        azimuth_deg = (azimuth_deg + 360) % 360
        
        return distance_km, azimuth_deg
