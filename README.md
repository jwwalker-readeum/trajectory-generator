# Demo Trajectory Generator Service

## ⚠️ IMPORTANT DISCLAIMER

**ALL VEHICLE PARAMETERS AND SIMULATION RESULTS IN THIS SERVICE ARE NOTIONAL DEMO VALUES ONLY.**

This is a demonstration service for educational and prototyping purposes. The vehicle configurations, trajectory simulations, and feasibility assessments **DO NOT** represent any real vehicle design, operational system, or actual performance characteristics. All numbers are purely illustrative placeholders.

## Purpose

This service provides a REST API for checking the feasibility of ballistic trajectories between launch and landing points. It uses a simplified 3-DOF point-mass simulation with a notional two-stage vehicle configuration.

**Use cases:**
- Demonstrating trajectory simulation concepts
- Prototyping web-based mission planning interfaces
- Educational examples of flight dynamics

## Features (Phase 1)

- **Vehicle Configuration**: YAML-based vehicle parameters with validation
- **3-DOF Simulation**: Point-mass trajectory with:
  - Two powered stages + coast period
  - Reentry vehicle (RV) separation
  - US Standard Atmosphere 1976
  - Drag coefficient vs Mach interpolation
  - Spherical rotating Earth model
  - G-load and Sutton-Graves stagnation heating
- **Reachability Sweep**: Offline parameter sweep to build feasibility envelope
- **Feasibility API**: REST endpoints to check if launch-landing pairs are achievable
- **Trajectory API**: Compute full time-series trajectory data

## Installation

### Requirements

- Python 3.11 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd <repo-directory>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the service:
```bash
# Option 1: Direct execution
python -m src.trajgen.main

# Option 2: Using uvicorn
cd src
uvicorn trajgen.main:app --reload --host 0.0.0.0 --port 8000
```

The service will:
- Load `vehicle_config.yaml`
- Build reachability sweep (cached to `.cache/sweep_cache.json`)
- Start API server on `http://localhost:8000`

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Endpoints

#### GET `/api/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "WARNING: NOTIONAL DEMO SERVICE - Results are for demonstration only"
}
```

#### GET `/api/config`

Get current vehicle configuration.

**Response:**
```json
{
  "config": {
    "vehicle": { ... },
    "aerodynamics": { ... },
    "limits": { ... }
  },
  "warning": "All values are NOTIONAL DEMO PLACEHOLDERS only"
}
```

#### PUT `/api/config`

Update vehicle configuration. Validates and saves the new config, then rebuilds the reachability sweep.

**Request body:** Full configuration object (same structure as GET response)

#### POST `/api/feasibility`

Check feasibility of a launch-landing pair.

**Request:**
```json
{
  "launch": {
    "lat": 28.5,
    "lon": -80.6
  },
  "landing": {
    "lat": 30.0,
    "lon": -70.0
  }
}
```

**Response (feasible):**
```json
{
  "feasible": true,
  "range_km": 1234.5,
  "azimuth_deg": 67.8,
  "reasons": ["All constraints satisfied"],
  "distance_to_envelope_km": 150.2,
  "peak_g_load": 28.3,
  "peak_heat_flux_w_cm2": 980.5,
  "warning": "NOTIONAL DEMO RESULT - Not representative of any real system"
}
```

**Response (infeasible - too far):**
```json
{
  "feasible": false,
  "range_km": 8500.0,
  "azimuth_deg": 45.0,
  "reasons": ["Range too far (8500.0 km > 6800.0 km maximum)"],
  "distance_to_envelope_km": 1700.0,
  "peak_g_load": null,
  "peak_heat_flux_w_cm2": null,
  "warning": "NOTIONAL DEMO RESULT - Not representative of any real system"
}
```

**Response (infeasible - constraint violation):**
```json
{
  "feasible": false,
  "range_km": 3500.0,
  "azimuth_deg": 90.0,
  "reasons": ["Peak g-load exceeds limit (45.2 > 40)"],
  "distance_to_envelope_km": 250.0,
  "peak_g_load": 45.2,
  "peak_heat_flux_w_cm2": 1200.0,
  "warning": "NOTIONAL DEMO RESULT - Not representative of any real system"
}
```

#### POST `/api/trajectory`

Compute full trajectory for a launch-landing pair (if feasible).

**Request:** Same as `/api/feasibility`

**Response:** Same as feasibility, plus `trajectory` field with time-series data:
```json
{
  "feasible": true,
  "range_km": 1234.5,
  "azimuth_deg": 67.8,
  "reasons": ["All constraints satisfied"],
  "distance_to_envelope_km": 150.2,
  "peak_g_load": 28.3,
  "peak_heat_flux_w_cm2": 980.5,
  "trajectory": [
    {
      "time_s": 0.0,
      "altitude_m": 10.0,
      "range_m": 0.0,
      "velocity_m_s": 0.1,
      "mach": 0.0,
      "g_load": 0.0,
      "heat_flux_w_cm2": 0.0,
      "latitude_deg": 28.5,
      "longitude_deg": -80.6,
      "flight_path_angle_deg": 45.0,
      "phase": "Stage 1"
    },
    ...
  ],
  "warning": "NOTIONAL DEMO RESULT - Not representative of any real system"
}
```

## Configuration

The vehicle configuration is stored in `vehicle_config.yaml` at the repository root. The configuration path can be overridden with the `VEHICLE_CONFIG_PATH` environment variable.

### Configuration Structure

```yaml
vehicle:
  name: demo-vehicle-v0
  stages:
    - name: stage_1
      mass_launch_kg: 6000
      mass_burnout_kg: 2600
      thrust_n: 180000
      isp_s: 250
      burn_time_s: 55
    - name: stage_2
      mass_launch_kg: 2200
      mass_burnout_kg: 800
      thrust_n: 60000
      isp_s: 280
      burn_time_s: 50
  stage_separation_coast_s: 3
  reentry_vehicle:
    mass_kg: 400
    separates_after: stage_2_burnout
  launch:
    angle_range_deg: [20, 85]
    azimuth_handled_by: landing_point_bearing

aerodynamics:
  reference_area_m2: 0.3
  cd_vs_mach:
    - [0.0, 0.30]
    - [1.0, 0.55]
    - [3.0, 0.40]
    - [8.0, 0.30]
  reentry_ballistic_coeff_kg_m2: 4000
  nose_radius_m: 0.05

limits:
  max_g_load: 40
  max_stagnation_heat_flux_w_cm2: 1500

environment:
  atmosphere: us_standard_1976
  earth_model: spherical_rotating

sweep:
  launch_angle_step_deg: 1
  burn_param_step: 0.05
```

## Model Assumptions and Limitations

### Simplifications

1. **Point Mass**: Vehicle is treated as a single point with no attitude dynamics
2. **3-DOF**: Motion in vertical plane only (range, altitude, velocity)
3. **Gravity Turn**: After initial pitch-over, thrust vector aligns with velocity vector
4. **Spherical Earth**: No oblateness, simple r^-2 gravity
5. **Standard Atmosphere**: US Standard 1976, no weather/wind effects
6. **Fixed Azimuth**: Launch azimuth determined by great circle to landing point
7. **Simplified Heating**: Sutton-Graves correlation for stagnation point only

### Physics Models

- **Atmosphere**: US Standard Atmosphere 1976 (up to 85 km)
- **Drag**: Cd interpolated from Mach table, using reference area
- **Heating**: Sutton-Graves: q = 1.7415e-4 × sqrt(ρ/R_n) × v³ (SI units)
- **Gravity**: g = g₀ × (R_earth / r)²
- **Earth Rotation**: Approximate centrifugal effect included

### Guidance

The simulation uses a **gravity turn** approach:
- Initial launch angle set by parameter sweep
- After pitch-over, thrust vector aligns with velocity vector
- Natural trajectory shaping from aerodynamics and gravity

### Constraints

Feasibility requires:
1. Kinematic reachability (within min/max range envelope)
2. Peak g-load < configured limit
3. Peak stagnation heat flux < configured limit

## Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

Test coverage includes:
- Configuration loading and validation
- Atmosphere model sanity checks
- Sutton-Graves heating formula verification
- Simulation execution and phase transitions
- Sweep building and caching
- Feasibility outcomes (reachable, too close, too far, g-limit, heat-limit)
- API endpoints with TestClient

## Development

### Project Structure

```
.
├── vehicle_config.yaml       # Vehicle configuration
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container definition (for Phase 3)
├── src/
│   └── trajgen/
│       ├── __init__.py
│       ├── config.py        # Configuration loading/validation
│       ├── atmosphere.py    # US Standard Atmosphere 1976
│       ├── simulation.py    # 3-DOF trajectory simulation
│       ├── sweep.py         # Reachability sweep
│       ├── feasibility.py   # Feasibility checking
│       ├── api.py          # FastAPI endpoints
│       └── main.py         # Application entrypoint
├── tests/
│   ├── test_config.py
│   ├── test_atmosphere.py
│   ├── test_simulation.py
│   ├── test_sweep.py
│   ├── test_feasibility.py
│   └── test_api.py
└── .github/
    └── workflows/
        └── ci.yml          # GitHub Actions CI

```

### Future Phases

**Phase 2** (not yet implemented):
- Web UI with Leaflet/OSM map for point selection
- Charts for trajectory visualization
- CesiumJS 3D trajectory overlay
- Password authentication
- Advanced settings editor

**Phase 3** (not yet implemented):
- Railway deployment configuration
- Production-ready containerization
- Static file serving for UI

The codebase is structured to support these additions with minimal refactoring.

## License

This is a demonstration project. See repository license for details.

## Contributing

This is Phase 1 of a demo service. Contributions welcome, but please remember all values are notional placeholders for demonstration only.
