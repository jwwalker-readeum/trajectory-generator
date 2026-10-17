"""Tests for atmosphere model."""

import pytest
import numpy as np

from src.trajgen.atmosphere import USStandardAtmosphere1976


def test_atmosphere_sea_level():
    """Test atmosphere at sea level."""
    atm = USStandardAtmosphere1976()
    
    # Sea level values
    T = atm.temperature(0)
    P = atm.pressure(0)
    rho = atm.density(0)
    
    # Check against known values
    assert abs(T - 288.15) < 0.1  # ~15°C
    assert abs(P - 101325) < 100  # ~1 atm
    assert abs(rho - 1.225) < 0.01  # Standard density


def test_atmosphere_altitude():
    """Test atmosphere at various altitudes."""
    atm = USStandardAtmosphere1976()
    
    # 10 km altitude
    T_10km = atm.temperature(10000)
    P_10km = atm.pressure(10000)
    rho_10km = atm.density(10000)
    
    # Values should decrease with altitude
    assert T_10km < 288.15
    assert P_10km < 101325
    assert rho_10km < 1.225
    
    # 30 km altitude
    rho_30km = atm.density(30000)
    assert rho_30km < rho_10km  # Density decreases with altitude


def test_speed_of_sound():
    """Test speed of sound calculation."""
    atm = USStandardAtmosphere1976()
    
    # Sea level
    a_sl = atm.speed_of_sound(0)
    assert 340 < a_sl < 345  # ~340 m/s at sea level
    
    # High altitude (lower temperature -> lower speed of sound)
    a_10km = atm.speed_of_sound(10000)
    assert a_10km < a_sl


def test_negative_altitude():
    """Test behavior at negative altitudes."""
    atm = USStandardAtmosphere1976()
    
    # Should handle negative altitude gracefully
    P_neg = atm.pressure(-100)
    assert P_neg >= 101325  # Should be at least sea level pressure
