"""3-DOF point-mass trajectory simulation.

NOTIONAL DEMO IMPLEMENTATION - All results are for demonstration only.

Simulation approach:
- Point-mass 3-DOF in vertical plane (range, altitude, velocity)
- Linear pitch program: maintains initial angle until threshold altitude/velocity,
  then gradually pitches down to achieve ballistic trajectory
- Two powered stages with coast period between
- RV separation after stage 2 burnout
- Spherical rotating Earth model
- US Standard Atmosphere 1976
- Cd interpolated vs Mach number
- Sutton-Graves stagnation heating model
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import interp1d
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass

from .atmosphere import USStandardAtmosphere1976
from .config import VehicleConfig


# Earth parameters
EARTH_RADIUS_M = 6371000.0  # meters
EARTH_ROTATION_RATE = 7.2921159e-5  # rad/s
G0 = 9.80665  # Standard gravity m/s^2

# Sutton-Graves heating constant (SI units: W·s^3/(kg^0.5·m^2.5))
SUTTON_GRAVES_K = 1.7415e-4


@dataclass
class TrajectoryPoint:
    """Single point along trajectory."""
    time_s: float
    altitude_m: float
    range_m: float
    velocity_m_s: float
    mach: float
    g_load: float
    heat_flux_w_cm2: float
    latitude_deg: float
    longitude_deg: float
    flight_path_angle_deg: float
    phase: str


class TrajectorySimulation:
    """3-DOF trajectory simulation."""
    
    def __init__(self, config: VehicleConfig):
        """Initialize simulation with vehicle configuration.
        
        Args:
            config: Vehicle configuration
        """
        self.config = config
        self.atmosphere = USStandardAtmosphere1976()
        
        # Build Cd interpolator
        cd_data = np.array(config['aerodynamics']['cd_vs_mach'])
        self._cd_interp = interp1d(
            cd_data[:, 0], cd_data[:, 1],
            kind='linear',
            bounds_error=False,
            fill_value=(cd_data[0, 1], cd_data[-1, 1])
        )
    
    def cd(self, mach: float) -> float:
        """Get drag coefficient at Mach number."""
        return float(self._cd_interp(mach))
    
    def simulate(
        self,
        launch_angle_deg: float,
        burn_param: float,
        launch_lat: float,
        launch_lon: float,
        azimuth_deg: float
    ) -> Tuple[bool, List[TrajectoryPoint], str]:
        """Run trajectory simulation.
        
        Args:
            launch_angle_deg: Initial launch angle from horizontal
            burn_param: Burn parameter (0-1, can scale thrust or burn time)
            launch_lat: Launch latitude in degrees
            launch_lon: Launch longitude in degrees
            azimuth_deg: Launch azimuth in degrees from north
            
        Returns:
            (success, trajectory_points, error_message)
        """
        vehicle = self.config['vehicle']
        aero = self.config['aerodynamics']
        
        # Initial state: [range, altitude, velocity, flight_path_angle, mass]
        # Start at small altitude with small initial velocity
        state0 = np.array([
            0.0,  # range (m)
            1.0,  # altitude (m) - start very low
            1.0,  # velocity (m/s) - small initial velocity
            np.radians(launch_angle_deg),  # flight path angle (rad)
            vehicle['stages'][0]['mass_launch_kg']  # mass (kg)
        ])
        
        trajectory = []
        current_time = 0.0
        current_state = state0.copy()
        initial_angle_rad = np.radians(launch_angle_deg)
        
        # Stage 1
        success, points, state, error = self._simulate_stage(
            current_state, current_time, vehicle['stages'][0],
            burn_param, launch_lat, launch_lon, azimuth_deg, "Stage 1", initial_angle_rad
        )
        if not success:
            return False, [], error
        trajectory.extend(points)
        current_time = points[-1].time_s
        current_state = state
        
        # Coast
        coast_time = vehicle['stage_separation_coast_s']
        success, points, state, error = self._simulate_coast(
            current_state, current_time, coast_time,
            launch_lat, launch_lon, azimuth_deg, "Coast", initial_angle_rad
        )
        if not success:
            return False, [], error
        trajectory.extend(points)
        current_time = points[-1].time_s
        current_state = state
        
        # Update mass for stage 2 ignition
        current_state[4] = vehicle['stages'][1]['mass_launch_kg']
        
        # Stage 2
        success, points, state, error = self._simulate_stage(
            current_state, current_time, vehicle['stages'][1],
            burn_param, launch_lat, launch_lon, azimuth_deg, "Stage 2", initial_angle_rad
        )
        if not success:
            return False, [], error
        trajectory.extend(points)
        current_time = points[-1].time_s
        current_state = state
        
        # RV separation - update mass
        rv_mass = vehicle['reentry_vehicle']['mass_kg']
        current_state[4] = rv_mass
        
        # RV reentry
        success, points, state, error = self._simulate_reentry(
            current_state, current_time, rv_mass,
            launch_lat, launch_lon, azimuth_deg, "Reentry", initial_angle_rad
        )
        if not success:
            return False, [], error
        trajectory.extend(points)
        
        return True, trajectory, ""
    
    def _equations_of_motion(
        self,
        t: float,
        state: np.ndarray,
        thrust_n: float,
        mass_flow_kg_s: float,
        mass_current: float,
        initial_angle_rad: float,
        use_ballistic_coeff: bool = False
    ) -> np.ndarray:
        """Equations of motion for powered or ballistic flight.
        
        State: [range, altitude, velocity, flight_path_angle, mass]
        """
        r, h, v, gamma, m = state
        
        if h < 0:
            return np.zeros(5)
        
        # Atmospheric properties
        rho = self.atmosphere.density(h)
        a_sound = self.atmosphere.speed_of_sound(h)
        mach = v / a_sound if a_sound > 0 else 0
        
        # Drag
        if use_ballistic_coeff:
            # Ballistic coefficient for RV
            beta = self.config['aerodynamics']['reentry_ballistic_coeff_kg_m2']
            drag = 0.5 * rho * v**2 * (m / beta)
        else:
            cd = self.cd(mach)
            S_ref = self.config['aerodynamics']['reference_area_m2']
            drag = 0.5 * rho * v**2 * cd * S_ref
        
        # Gravity (spherical Earth)
        R = EARTH_RADIUS_M + h
        g = G0 * (EARTH_RADIUS_M / R)**2
        
        # Accelerations
        if m > 0:
            a_thrust = thrust_n / m
            a_drag = drag / m
        else:
            a_thrust = 0
            a_drag = 0
        
        # Flight dynamics
        # Thrust aligned with velocity direction
        dv_dt = a_thrust - a_drag - g * np.sin(gamma)
        
        # d(flight_path_angle)/dt
        # Linear pitch program for powered flight
        if thrust_n > 0:
            # Hold initial angle until reaching altitude threshold, then pitch down
            if h < 20000:  # Below 20 km, hold initial angle
                dgamma_dt = 0
            elif h < 80000:  # 20-80 km, gradual pitch down
                dgamma_dt = -0.01  # rad/s pitch rate
            else:
                # Above 80 km, let trajectory naturally turn
                a_centrifugal = v**2 / R if v > 0 else 0
                dgamma_dt = (a_centrifugal - g * np.cos(gamma)) / v if v > 0 else 0
        else:
            # Unpowered: natural trajectory curvature
            if v > 1.0:
                a_centrifugal = v**2 / R
                dgamma_dt = (a_centrifugal - g * np.cos(gamma)) / v
            else:
                dgamma_dt = 0
        
        # d(altitude)/dt
        dh_dt = v * np.sin(gamma)
        
        # d(range)/dt (ground track distance)
        dr_dt = v * np.cos(gamma) * R / (R + h) if R + h > 0 else 0
        
        # d(mass)/dt
        dm_dt = -mass_flow_kg_s
        
        return np.array([dr_dt, dh_dt, dv_dt, dgamma_dt, dm_dt])
    
    def _simulate_stage(
        self,
        state0: np.ndarray,
        t0: float,
        stage_config: Dict[str, Any],
        burn_param: float,
        launch_lat: float,
        launch_lon: float,
        azimuth_deg: float,
        phase_name: str,
        initial_angle_rad: float
    ) -> Tuple[bool, List[TrajectoryPoint], np.ndarray, str]:
        """Simulate a powered stage."""
        thrust = stage_config['thrust_n'] * burn_param
        burn_time = stage_config['burn_time_s']
        mass_flow = (stage_config['mass_launch_kg'] - stage_config['mass_burnout_kg']) / burn_time
        
        def eom(t, y):
            return self._equations_of_motion(t, y, thrust, mass_flow, y[4], initial_angle_rad)
        
        def event_ground(t, y):
            return y[1]  # altitude
        event_ground.terminal = True
        
        try:
            sol = solve_ivp(
                eom,
                (t0, t0 + burn_time),
                state0,
                method='RK45',
                events=event_ground,
                max_step=1.0,
                rtol=1e-6
            )
        except Exception as e:
            return False, [], state0, f"Integration failed in {phase_name}: {str(e)}"
        
        if not sol.success:
            return False, [], state0, f"Integration failed in {phase_name}"
        
        points = self._extract_trajectory_points(
            sol.t, sol.y, launch_lat, launch_lon, azimuth_deg, phase_name
        )
        
        if len(points) == 0:
            return False, [], state0, f"No valid points in {phase_name}"
        
        final_state = sol.y[:, -1]
        
        return True, points, final_state, ""
    
    def _simulate_coast(
        self,
        state0: np.ndarray,
        t0: float,
        coast_time: float,
        launch_lat: float,
        launch_lon: float,
        azimuth_deg: float,
        phase_name: str,
        initial_angle_rad: float
    ) -> Tuple[bool, List[TrajectoryPoint], np.ndarray, str]:
        """Simulate coast phase."""
        def eom(t, y):
            return self._equations_of_motion(t, y, 0.0, 0.0, y[4], initial_angle_rad)
        
        def event_ground(t, y):
            return y[1]
        event_ground.terminal = True
        
        try:
            sol = solve_ivp(
                eom,
                (t0, t0 + coast_time),
                state0,
                method='RK45',
                events=event_ground,
                max_step=1.0,
                rtol=1e-6
            )
        except Exception as e:
            return False, [], state0, f"Integration failed in {phase_name}: {str(e)}"
        
        if not sol.success:
            return False, [], state0, f"Integration failed in {phase_name}"
        
        points = self._extract_trajectory_points(
            sol.t, sol.y, launch_lat, launch_lon, azimuth_deg, phase_name
        )
        
        final_state = sol.y[:, -1]
        
        return True, points, final_state, ""
    
    def _simulate_reentry(
        self,
        state0: np.ndarray,
        t0: float,
        rv_mass: float,
        launch_lat: float,
        launch_lon: float,
        azimuth_deg: float,
        phase_name: str,
        initial_angle_rad: float
    ) -> Tuple[bool, List[TrajectoryPoint], np.ndarray, str]:
        """Simulate RV reentry with ballistic coefficient."""
        def eom(t, y):
            return self._equations_of_motion(t, y, 0.0, 0.0, rv_mass, initial_angle_rad, use_ballistic_coeff=True)
        
        def event_ground(t, y):
            return y[1]  # altitude - stop at ground
        event_ground.terminal = True
        event_ground.direction = -1
        
        try:
            sol = solve_ivp(
                eom,
                (t0, t0 + 1200),  # Max 20 minutes for reentry
                state0,
                method='RK45',
                events=event_ground,
                max_step=1.0,
                rtol=1e-6
            )
        except Exception as e:
            return False, [], state0, f"Integration failed in {phase_name}: {str(e)}"
        
        points = self._extract_trajectory_points(
            sol.t, sol.y, launch_lat, launch_lon, azimuth_deg, phase_name
        )
        
        if len(points) == 0:
            return False, [], state0, f"No valid points in {phase_name}"
        
        final_state = sol.y[:, -1]
        
        return True, points, final_state, ""
    
    def _extract_trajectory_points(
        self,
        times: np.ndarray,
        states: np.ndarray,
        launch_lat: float,
        launch_lon: float,
        azimuth_deg: float,
        phase: str
    ) -> List[TrajectoryPoint]:
        """Extract trajectory points from integration results."""
        points = []
        
        for i in range(len(times)):
            t = times[i]
            r, h, v, gamma, m = states[:, i]
            
            if h < 0:
                h = 0
            
            # Atmospheric properties
            rho = self.atmosphere.density(h)
            a_sound = self.atmosphere.speed_of_sound(h)
            mach = v / a_sound if a_sound > 0 else 0
            
            # g-load (excluding gravity)
            # Approximate from drag + centripetal
            cd = self.cd(mach)
            S_ref = self.config['aerodynamics']['reference_area_m2']
            drag = 0.5 * rho * v**2 * cd * S_ref
            if m > 0:
                g_load = drag / (m * G0)
            else:
                g_load = 0
            
            # Add centripetal acceleration contribution
            R = EARTH_RADIUS_M + h
            if v > 0 and R > 0:
                g_load += (v**2 / R) / G0
            
            # Sutton-Graves stagnation heating
            # q = k * sqrt(rho / R_n) * v^3
            R_n = self.config['aerodynamics']['nose_radius_m']
            if rho > 0 and v > 500:  # Only compute for significant heating
                heat_flux = SUTTON_GRAVES_K * np.sqrt(rho / R_n) * v**3
                heat_flux_w_cm2 = heat_flux / 10000  # Convert W/m^2 to W/cm^2
            else:
                heat_flux_w_cm2 = 0
            
            # Compute lat/lon along great circle
            # Simplified: assume flat projection for now
            range_km = r / 1000.0
            lat, lon = self._compute_position(launch_lat, launch_lon, range_km, azimuth_deg)
            
            points.append(TrajectoryPoint(
                time_s=t,
                altitude_m=h,
                range_m=r,
                velocity_m_s=v,
                mach=mach,
                g_load=g_load,
                heat_flux_w_cm2=heat_flux_w_cm2,
                latitude_deg=lat,
                longitude_deg=lon,
                flight_path_angle_deg=np.degrees(gamma),
                phase=phase
            ))
        
        return points
    
    def _compute_position(
        self,
        lat0: float,
        lon0: float,
        range_km: float,
        azimuth_deg: float
    ) -> Tuple[float, float]:
        """Compute position along great circle.
        
        Args:
            lat0: Starting latitude (degrees)
            lon0: Starting longitude (degrees)
            range_km: Ground range (km)
            azimuth_deg: Azimuth from north (degrees)
            
        Returns:
            (latitude, longitude) in degrees
        """
        # Convert to radians
        lat1_rad = np.radians(lat0)
        lon1_rad = np.radians(lon0)
        azimuth_rad = np.radians(azimuth_deg)
        
        # Angular distance
        delta = range_km / (EARTH_RADIUS_M / 1000.0)
        
        # Great circle formula
        lat2_rad = np.arcsin(
            np.sin(lat1_rad) * np.cos(delta) +
            np.cos(lat1_rad) * np.sin(delta) * np.cos(azimuth_rad)
        )
        
        lon2_rad = lon1_rad + np.arctan2(
            np.sin(azimuth_rad) * np.sin(delta) * np.cos(lat1_rad),
            np.cos(delta) - np.sin(lat1_rad) * np.sin(lat2_rad)
        )
        
        return np.degrees(lat2_rad), np.degrees(lon2_rad)
    
    def get_peak_values(self, trajectory: List[TrajectoryPoint]) -> Dict[str, float]:
        """Extract peak values from trajectory.
        
        Returns:
            Dictionary with peak g-load and heat flux
        """
        if not trajectory:
            return {'peak_g_load': 0, 'peak_heat_flux_w_cm2': 0}
        
        peak_g = max(p.g_load for p in trajectory)
        peak_heat = max(p.heat_flux_w_cm2 for p in trajectory)
        
        return {
            'peak_g_load': peak_g,
            'peak_heat_flux_w_cm2': peak_heat
        }
