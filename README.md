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

## Features

### Phase 1 (API Backend)

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

### Phase 2 (Web UI)

- **Password Gate**: Simple authentication for single-user demo deployment
- **Interactive Map**: Leaflet + OpenStreetMap for selecting launch and landing points
- **Real-time Feasibility**: Click-to-check if mission is within vehicle envelope
- **Trajectory Visualization**: 
  - Altitude vs Range charts
  - Altitude vs Mach charts
  - Real-time constraint checking (g-load, heating)
- **3D Flyout**: CesiumJS 3D globe visualization of trajectory path
- **Advanced Settings**: In-UI editor for vehicle configuration with live validation
- **Mobile-Responsive**: Works on tablets and mobile devices

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

3. Set environment variables (optional):
```bash
# Enable password authentication (recommended for deployment)
export APP_PASSWORD="your_secure_password"

# Optional: Cesium Ion token for enhanced 3D imagery
export CESIUM_ION_TOKEN="your_cesium_token"

# Optional: Custom vehicle config path
export VEHICLE_CONFIG_PATH="/path/to/config.yaml"
```

4. Run the service:
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
- Start web server on `http://localhost:8000`

### Accessing the UI

1. Open your browser to `http://localhost:8000`
2. If `APP_PASSWORD` is set, enter the password at the login screen
3. Use the interactive map to select launch and landing points
4. Check feasibility or compute full trajectory with visualization

## Authentication

The service supports simple password authentication for single-user demo deployment:

- **Password Gate**: Set `APP_PASSWORD` environment variable to require login
- **Session Management**: Uses HTTP cookies (24-hour expiry)
- **Public Endpoints**: Health check and login page remain accessible
- **Development**: Leave `APP_PASSWORD` unset to disable authentication

**Note**: This is a simple demo authentication system. For production use, implement proper user management, HTTPS, and secure session storage.

## API Documentation

The REST API is still available for programmatic access. Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

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

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_PASSWORD` | No | None | Password for UI access. If not set, authentication is disabled |
| `CESIUM_ION_TOKEN` | No | Default | Cesium Ion access token for enhanced 3D imagery |
| `VEHICLE_CONFIG_PATH` | No | `./vehicle_config.yaml` | Path to vehicle configuration file |

### Vehicle Configuration

The vehicle configuration is stored in `vehicle_config.yaml` at the repository root. The configuration path can be overridden with the `VEHICLE_CONFIG_PATH` environment variable.

### Notional Parameter Tuning

The default notional vehicle parameters have been tuned to produce **ICBM-scale demonstration ranges** (~400-3000 km ground range) suitable for map-based visualization. Key adjustments from initial placeholder values:

- **Burn times**: Increased to 65s for both stages (from 55s/50s) for longer powered flight
- **Specific impulse**: Improved to 265s/295s (from 250s/280s) for higher efficiency
- **Mass ratios**: Adjusted for better performance while maintaining structural feasibility
- **Nose radius**: Increased to 0.10m (from 0.05m) to reduce Sutton-Graves stagnation heating
- **Ballistic coefficient**: Increased to 5000 kg/m² (from 4000) for better reentry characteristics

These changes keep the simulation within the configured limits (g-load < 40, heat flux < 1500 W/cm²) while producing useful demonstration trajectories.

### Configuration Structure

```yaml
vehicle:
  name: demo-vehicle-v0
  stages:
    - name: stage_1
      mass_launch_kg: 6000
      mass_burnout_kg: 2200
      thrust_n: 180000
      isp_s: 265
      burn_time_s: 65
    - name: stage_2
      mass_launch_kg: 2200
      mass_burnout_kg: 700
      thrust_n: 65000
      isp_s: 295
      burn_time_s: 65
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

## Railway Deployment (Phase 3)

This repository is configured for easy deployment to [Railway](https://railway.app) using Docker. **This PR prepares the deployment configuration but does NOT deploy any live service.**

### Prerequisites

- A Railway account (free tier available at [railway.app](https://railway.app))
- GitHub repository access
- Basic understanding of Railway's pricing model

### Deployment Steps

1. **Connect Repository to Railway**
   - Log in to Railway dashboard
   - Click **"New Project"** → **"Deploy from GitHub repo"**
   - Select this repository from the list
   - Railway will automatically detect the `Dockerfile` and `railway.json`

2. **Configure Environment Variables**
   - In the Railway project dashboard, go to **Variables** tab
   - Add required/optional variables:

   **Optional (recommended for Phase 2+ UI):**
   - `APP_PASSWORD` - Password to gate web UI access in production (leave unset for API-only or local dev)
   
   **Optional (for CesiumJS 3D visualization in Phase 2+):**
   - `CESIUM_ION_TOKEN` - Free token from [cesium.com/ion/tokens](https://cesium.com/ion/tokens)
   
   **Optional (to override default config):**
   - `VEHICLE_CONFIG_PATH` - Path to vehicle config (defaults to `/app/vehicle_config.yaml`)
   
   **Automatic:**
   - `PORT` - Railway automatically provides this, do not set manually

3. **Deploy**
   - Railway automatically builds and deploys on push to `main` branch
   - Initial build takes ~2-3 minutes
   - Monitor deployment in the **Deployments** tab

4. **Generate Domain**
   - Go to **Settings** → **Networking**
   - Click **"Generate Domain"** for a public `*.up.railway.app` URL
   - Or add a custom domain if desired

5. **Verify Deployment**
   - Visit `https://your-app.up.railway.app/api/health`
   - Should return `{"status": "healthy", "message": "WARNING: NOTIONAL DEMO SERVICE..."}`
   - API documentation available at `/docs`

### Cost Estimation

**Railway Pricing Model** (as of October 2024):
- **Free Trial**: $5 USD credit (one-time)
- **Hobby Plan**: $5/month for 500 hours ($0.01/hour)
- **Pro Plan**: Pay-as-you-go, ~$10-20/month for a small web service

**Expected Usage**:
- This service is a **lightweight Python web API** with minimal compute
- Typical usage: **Small web service class** (~512 MB RAM, minimal CPU)
- Estimated cost: **$5-10/month on Hobby plan** for moderate traffic
- Free tier credits cover initial testing and low-volume use

**Cost Optimization**:
- Service sleeps automatically when idle on Railway
- No database or heavy compute requirements
- Sweep cache stored in-memory (ephemeral storage)

### Railway Configuration Files

This repository includes:

- **`Dockerfile`**: Production-ready container with:
  - Binds to `0.0.0.0` (required for Railway)
  - Honors `$PORT` environment variable from Railway
  - Health check endpoint (`/api/health`)
  - Copies `vehicle_config.yaml` and `static/` files (when present)

- **`railway.json`**: Railway deployment configuration:
  - Uses Dockerfile builder (not Nixpacks)
  - Single replica with auto-restart on failure
  - Health check monitoring

- **`.env.example`**: Environment variable template for reference

### Deployment Notes

- **This PR does NOT deploy a live service** - it only prepares the configuration
- Railway auto-deploys from `main` branch after initial setup
- All simulation results remain **NOTIONAL DEMO VALUES** in production
- For local development, continue using `uvicorn` directly (see Installation section)

### Troubleshooting

**Build Failures:**
- Check Railway build logs in the **Deployments** tab
- Verify `requirements.txt` dependencies are compatible with Python 3.11

**Service Won't Start:**
- Verify health check passes: `/api/health` should return 200 OK
- Check Railway service logs for startup errors
- Ensure `VEHICLE_CONFIG_PATH` is not set incorrectly

**Performance Issues:**
- Initial sweep build takes ~10-30 seconds on startup (cached afterward)
- Consider upgrading Railway plan if hitting memory/CPU limits
- Monitor resource usage in Railway metrics dashboard

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

The simulation uses a **linear pitch program** for ICBM-scale trajectories:
- Initial launch angle set by parameter sweep (20-85°)
- **Below 20 km altitude**: Hold initial launch angle (vertical climb phase)
- **20-80 km altitude**: Gradual pitch-down at 0.01 rad/s (pitch-over phase)
- **Above 80 km**: Natural ballistic arc from centrifugal and gravity effects
- Thrust always aligned with velocity vector (zero angle of attack assumption)

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

## Using the Web Interface

### Mission Planning Workflow

1. **Set Launch Point**: Click on the map to place a launch marker (🚀)
2. **Set Landing Point**: Click again to place a landing marker (🎯)
3. **Check Feasibility**: Click "Check Feasibility" to see if the mission is achievable
   - View range, azimuth, and envelope distance
   - See constraint violations (if any)
4. **Compute Trajectory**: Click "Compute Trajectory" for full simulation
   - View altitude vs range chart
   - View altitude vs Mach chart
   - See peak g-load and heating values
5. **3D Visualization**: Click "View 3D" to see trajectory on Cesium globe
6. **Adjust Vehicle**: Click "⚙️ Settings" to modify vehicle parameters
   - Edit configuration JSON
   - System automatically rebuilds sweep on save

### Tips

- **Clear Markers**: Use the "Clear Markers" button to reset
- **Mobile**: The UI is touch-friendly for tablet/mobile use
- **Range**: Default vehicle targets ~400-3000 km demonstration ranges
- **Constraints**: Watch for g-load and heating limit violations in red

## Development

### Project Structure

```
.
├── vehicle_config.yaml       # Vehicle configuration
├── requirements.txt          # Python dependencies
├── Dockerfile               # Production container (Phase 2+3)
├── railway.json             # Railway deployment config (Phase 3)
├── .env.example             # Environment variable template
├── src/
│   └── trajgen/
│       ├── __init__.py
│       ├── config.py        # Configuration loading/validation
│       ├── atmosphere.py    # US Standard Atmosphere 1976
│       ├── simulation.py    # 3-DOF trajectory simulation
│       ├── sweep.py         # Reachability sweep
│       ├── feasibility.py   # Feasibility checking
│       ├── api.py          # FastAPI endpoints + UI serving
│       ├── auth.py         # Password authentication middleware
│       └── main.py         # Application entrypoint
├── static/
│   ├── index.html          # Main UI
│   ├── login.html          # Login page
│   ├── style.css           # Styling
│   └── app.js              # Client-side application logic
├── tests/
│   ├── test_config.py
│   ├── test_atmosphere.py
│   ├── test_simulation.py
│   ├── test_sweep.py
│   ├── test_feasibility.py
│   ├── test_api.py
│   └── test_auth.py        # Authentication tests
└── .github/
    └── workflows/
        └── ci.yml          # GitHub Actions CI

```

### Future Phases

**Phase 3** (this PR - deployment prep):
- Railway deployment configuration ✅
- Production-ready containerization ✅
- Environment variable documentation ✅
- Deployment guide ✅
- **Note**: No live service deployed - configuration only

**Phase 4** (future):
- Actual Railway deployment (by maintainer)
- Production monitoring and logging
- Enhanced error handling and resilience

The codebase is structured to support these additions with minimal refactoring.

## License

This is a demonstration project. See repository license for details.

## Contributing

This is Phase 1 of a demo service. Contributions welcome, but please remember all values are notional placeholders for demonstration only.
