"""Tests for trajectory simulation."""

import pytest
import numpy as np

from src.trajgen.config import VehicleConfig
from src.trajgen.simulation import TrajectorySimulation, SUTTON_GRAVES_K


def test_simulation_initialization():
    """Test simulation initialization."""
    config = VehicleConfig()
    sim = TrajectorySimulation(config)
    
    assert sim.config is not None
    assert sim.atmosphere is not None


def test_cd_interpolation():
    """Test drag coefficient interpolation."""
    config = VehicleConfig()
    sim = TrajectorySimulation(config)
    
    # Test known points
    cd_0 = sim.cd(0.0)
    cd_1 = sim.cd(1.0)
    cd_3 = sim.cd(3.0)
    
    assert abs(cd_0 - 0.30) < 0.01
    assert abs(cd_1 - 0.55) < 0.01
    assert abs(cd_3 - 0.40) < 0.01
    
    # Test interpolation
    cd_2 = sim.cd(2.0)
    assert 0.40 < cd_2 < 0.55


def test_sutton_graves_heating():
    """Test Sutton-Graves heating formula with known values."""
    # Test parameters
    rho = 0.1  # kg/m^3
    R_n = 0.05  # m
    v = 3000  # m/s
    
    # q = k * sqrt(rho / R_n) * v^3
    q_expected = SUTTON_GRAVES_K * np.sqrt(rho / R_n) * v**3
    
    # Should be on order of MW/m^2 for reentry conditions
    assert q_expected > 1e6  # > 1 MW/m^2
    
    # W/cm^2
    q_w_cm2 = q_expected / 10000
    assert q_w_cm2 > 100


def test_simulation_basic():
    """Test basic simulation execution."""
    config = VehicleConfig()
    sim = TrajectorySimulation(config)
    
    # Run a nominal simulation
    success, trajectory, error = sim.simulate(
        launch_angle_deg=45.0,
        burn_param=1.0,
        launch_lat=28.5,
        launch_lon=-80.6,
        azimuth_deg=90.0
    )
    
    assert success, f"Simulation failed: {error}"
    assert len(trajectory) > 0, "No trajectory points generated"
    
    # Check trajectory structure
    point = trajectory[0]
    assert hasattr(point, 'time_s')
    assert hasattr(point, 'altitude_m')
    assert hasattr(point, 'velocity_m_s')
    assert hasattr(point, 'g_load')
    assert hasattr(point, 'heat_flux_w_cm2')


def test_simulation_phases():
    """Test that simulation includes all phases."""
    config = VehicleConfig()
    sim = TrajectorySimulation(config)
    
    success, trajectory, error = sim.simulate(
        launch_angle_deg=45.0,
        burn_param=1.0,
        launch_lat=28.5,
        launch_lon=-80.6,
        azimuth_deg=90.0
    )
    
    assert success
    
    phases = set(p.phase for p in trajectory)
    assert 'Stage 1' in phases
    assert 'Stage 2' in phases
    assert 'Reentry' in phases


def test_peak_values():
    """Test peak value extraction."""
    config = VehicleConfig()
    sim = TrajectorySimulation(config)
    
    success, trajectory, error = sim.simulate(
        launch_angle_deg=45.0,
        burn_param=1.0,
        launch_lat=28.5,
        launch_lon=-80.6,
        azimuth_deg=90.0
    )
    
    assert success
    
    peaks = sim.get_peak_values(trajectory)
    assert 'peak_g_load' in peaks
    assert 'peak_heat_flux_w_cm2' in peaks
    assert peaks['peak_g_load'] > 0
    assert peaks['peak_heat_flux_w_cm2'] >= 0
