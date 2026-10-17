"""US Standard Atmosphere 1976 model.

Simple implementation for trajectory simulation.
"""

import numpy as np
from scipy.interpolate import interp1d


# US Standard Atmosphere 1976 - Geometric altitude (km) vs Temperature (K), Pressure (Pa)
# Data points up to 86 km
_ALTITUDE_KM = np.array([
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85
])

_TEMPERATURE_K = np.array([
    288.15, 281.65, 275.15, 268.65, 262.17, 255.68, 249.19, 242.70, 236.22, 229.73, 223.25,
    216.77, 216.65, 216.65, 216.65, 216.65, 216.65, 216.65, 216.65, 216.65, 216.65,
    221.55, 226.51, 236.51, 250.35, 264.16, 270.65, 260.77, 247.02, 233.29, 219.59, 208.40, 198.64, 188.89
])

_PRESSURE_PA = np.array([
    101325, 89874.6, 79495.2, 70108.5, 61640.2, 54019.9, 47181.0, 41060.7, 35599.8, 30742.5, 26436.3,
    22632.1, 19330.4, 16510.4, 14101.8, 12044.6, 10287.5, 8786.66, 7504.84, 6410.03, 5474.89,
    2511.02, 1171.87, 559.456, 277.522, 142.902, 79.7791, 42.5211, 21.9582, 10.9517, 5.22083, 2.38803, 1.05246, 0.44688
])

# Gas constant for dry air (J/kg/K)
R_AIR = 287.05


class USStandardAtmosphere1976:
    """US Standard Atmosphere 1976 model."""
    
    def __init__(self):
        """Initialize atmosphere model with interpolators."""
        self._temp_interp = interp1d(
            _ALTITUDE_KM * 1000,  # Convert to meters
            _TEMPERATURE_K,
            kind='linear',
            bounds_error=False,
            fill_value=(_TEMPERATURE_K[0], _TEMPERATURE_K[-1])
        )
        
        self._pressure_interp = interp1d(
            _ALTITUDE_KM * 1000,  # Convert to meters
            _PRESSURE_PA,
            kind='linear',
            bounds_error=False,
            fill_value=(_PRESSURE_PA[0], 0.0)  # Zero pressure above max altitude
        )
    
    def temperature(self, altitude_m: float) -> float:
        """Get temperature at altitude.
        
        Args:
            altitude_m: Geometric altitude in meters
            
        Returns:
            Temperature in Kelvin
        """
        return float(self._temp_interp(altitude_m))
    
    def pressure(self, altitude_m: float) -> float:
        """Get pressure at altitude.
        
        Args:
            altitude_m: Geometric altitude in meters
            
        Returns:
            Pressure in Pascals
        """
        if altitude_m < 0:
            return _PRESSURE_PA[0]
        return float(self._pressure_interp(altitude_m))
    
    def density(self, altitude_m: float) -> float:
        """Get density at altitude using ideal gas law.
        
        Args:
            altitude_m: Geometric altitude in meters
            
        Returns:
            Density in kg/m^3
        """
        T = self.temperature(altitude_m)
        P = self.pressure(altitude_m)
        return P / (R_AIR * T)
    
    def speed_of_sound(self, altitude_m: float) -> float:
        """Get speed of sound at altitude.
        
        Args:
            altitude_m: Geometric altitude in meters
            
        Returns:
            Speed of sound in m/s
        """
        T = self.temperature(altitude_m)
        gamma = 1.4  # Ratio of specific heats for air
        return np.sqrt(gamma * R_AIR * T)
