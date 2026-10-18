# Demo Trajectory Generator Service

## ⚠️ IMPORTANT DISCLAIMER

**ALL VEHICLE PARAMETERS AND SIMULATION RESULTS IN THIS SERVICE ARE NOTIONAL DEMO VALUES ONLY.**

This is a demonstration service for educational and prototyping purposes. The vehicle configurations, trajectory simulations, and feasibility assessments **DO NOT** represent any real vehicle design, operational system, or actual performance characteristics. All numbers are purely illustrative placeholders.

**Do not use this service for any real mission planning, engineering analysis, or operational decisions.**

---

## What Is This?

This service demonstrates a simplified 3-DOF (three-degree-of-freedom) ballistic trajectory simulator with an interactive web interface. It simulates a notional two-stage vehicle flying from a launch point to a landing point on Earth, accounting for:

- Two powered stages with coast phase
- Atmospheric drag and heating
- Earth's rotation and spherical geometry
- G-load and thermal constraints

**Use Cases:**
- Educational demonstrations of flight dynamics
- Prototyping mission planning interfaces
- Exploring trajectory simulation concepts
- Learning about API design for simulation services

**What It's NOT:**
- A real trajectory simulator for operational use
- Representative of any actual vehicle or system
- Suitable for safety-critical or production applications

---

## Features

### Phase 1: API Backend
- **Vehicle Configuration**: YAML-based parameters with validation
- **3-DOF Simulation**: Point-mass trajectory with atmospheric drag, heating, and gravity
- **Reachability Sweep**: Pre-computed envelope of feasible trajectories
- **REST API**: Check feasibility and compute full trajectories programmatically

### Phase 2: Web Interface
- **Interactive Map**: Click to set launch and landing points (Leaflet + OpenStreetMap)
- **Real-Time Feasibility**: Instant feedback on whether a mission is achievable
- **Trajectory Charts**: Altitude vs Range and Altitude vs Mach visualizations
- **3D Visualization**: CesiumJS globe view of trajectory path
- **Advanced Settings**: In-browser vehicle configuration editor
- **Password Authentication**: Simple login for demo deployments

### Phase 3: Railway Deployment (This PR)
- **Docker Configuration**: Production-ready containerization
- **Railway Integration**: One-command deployment to Railway hosting
- **Environment Variables**: Documented configuration for deployment
- **Health Checks**: Automated monitoring for production readiness

---

## Prerequisites

### For Local Development

- **Python 3.11 or higher** (required)
  - Check your version: `python3 --version`
  - Download from [python.org](https://www.python.org/downloads/) if needed

- **pip** (Python package manager, included with Python)

- **Git** (to clone the repository)

### For Docker Deployment (Optional)

- **Docker** (if you want to run in a container locally)
  - Download from [docker.com](https://www.docker.com/get-started)

### For Railway Deployment (Optional)

- **Railway Account** (free tier available)
  - Sign up at [railway.app](https://railway.app)

- **GitHub Account** (to connect repository to Railway)

---

## Local Setup and Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/trajectory-generator.git
cd trajectory-generator
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pyyaml` - Configuration parsing
- `numpy` - Numerical computations
- `scipy` - Scientific computing
- `pydantic` - Data validation
- `pytest` - Testing framework

### Step 4: Configure Environment Variables (Optional)

**The service automatically loads environment variables from a `.env` file in the project root**, making it easy to configure credentials for local development without exporting shell variables.

Create a `.env` file:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your values (use any text editor)
nano .env
```

**Environment Variables:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `APP_PASSWORD` | No | None | Password for UI access. **Leave empty for local development** to disable authentication. Set a strong password for deployment. |
| `CESIUM_ION_TOKEN` | No | Default | Cesium Ion access token for enhanced 3D imagery. Get a free token at [cesium.com/ion/signup](https://cesium.com/ion/signup). The default token works but may have rate limits. |
| `VEHICLE_CONFIG_PATH` | No | `./vehicle_config.yaml` | Path to vehicle configuration file. Only change if using a custom config. |
| `PORT` | No | `8000` | Port for the web server. Railway provides this automatically in production. |

**Example `.env` for local development (authentication disabled):**

```bash
# Leave APP_PASSWORD unset for local dev - no login required
# APP_PASSWORD=

# Optional: Add your Cesium token for better 3D imagery
CESIUM_ION_TOKEN=your_token_here
```

**Example `.env` for testing with authentication:**

```bash
# Set a password to test the login screen
APP_PASSWORD=demo123

CESIUM_ION_TOKEN=your_token_here
```

**Important Notes:**

- **Values are loaded from `.env` automatically** when you run the service (via `python-dotenv`)
- **Existing environment variables take precedence** over `.env` values (important for Railway deployment)
- **No need to use quotes** around values in `.env` files (quotes are automatically stripped)
- **Whitespace is trimmed** from both keys and values
- **Never commit `.env` to git** (already in `.gitignore`)

### Step 5: Run the Service

```bash
# Option 1: Direct execution (recommended for development)
python -m src.trajgen.main

# Option 2: Using uvicorn directly
uvicorn trajgen.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:

```
================================================================================
DEMO TRAJECTORY GENERATOR SERVICE
================================================================================
WARNING: All vehicle parameters and simulation results are
         NOTIONAL DEMO VALUES ONLY for demonstration purposes.
         They do NOT represent any real vehicle or system.
================================================================================

Initializing trajectory generation service...
WARNING: All vehicle parameters and results are NOTIONAL DEMO VALUES ONLY
Loading vehicle configuration from: vehicle_config.yaml
Loaded configuration: demo-vehicle-v0
Loading sweep from cache...
Loaded sweep with 1234 entries
Service initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

The service will:
1. Load `vehicle_config.yaml` from the repository root
2. Build or load a reachability sweep (cached in `.cache/sweep_cache.json`)
3. Start the web server on `http://localhost:8000`

### Step 6: Access the Web Interface

1. Open your web browser to **`http://localhost:8000`**

2. **If you set `APP_PASSWORD`**: You'll see a login screen
   - Enter your password
   - Click "Login"
   - You'll be redirected to the main interface

3. **If `APP_PASSWORD` is not set**: You'll go directly to the main interface (no login required)

**You're ready to use the demo!** 🚀

---

## Using the Web Interface

### Mission Planning Workflow

#### 1. Set Launch Point
- Click anywhere on the map to place a **launch marker** (🚀 red rocket icon)
- The marker shows the launch coordinates
- Drag the marker to adjust the position

#### 2. Set Landing Point
- Click a second time on the map to place a **landing marker** (🎯 green target icon)
- The marker shows the landing coordinates
- Drag the marker to adjust the position

#### 3. Check Feasibility (Quick Check)
- Click the **"Check Feasibility"** button
- Results appear in the **Results Panel** (right side):
  - ✅ **Feasible**: Mission is achievable with current vehicle
    - Shows: Range, Azimuth, Peak G-load, Peak Heating
  - ❌ **Infeasible**: Mission violates constraints
    - Shows reasons: "Too far", "G-load exceeds limit", "Heating exceeds limit", etc.
- The feasibility check is **fast** (no full trajectory computation)

#### 4. Compute Full Trajectory
- Click the **"Compute Trajectory"** button
- Results appear with:
  - **Altitude vs Range Chart**: Trajectory profile in vertical plane
  - **Altitude vs Time Chart**: Altitude profile over mission duration
  - **Mach vs Time Chart**: Speed profile during flight
  - **Trajectory Details**: Phase breakdowns, peak values
  - Constraint violations highlighted in red if any
- This performs a **full simulation** and takes slightly longer

#### 5. View 3D Visualization
- After computing a trajectory, click **"View 3D"** button
- Opens a **CesiumJS 3D globe** overlay showing:
  - Launch and landing points
  - Trajectory path overlaid on Earth
  - Terrain and satellite imagery (if `CESIUM_ION_TOKEN` is set)
- Use mouse to:
  - **Left-drag**: Rotate globe
  - **Right-drag**: Pan
  - **Scroll**: Zoom in/out
- Click **"Close 3D View"** to return to the map

#### 6. Adjust Vehicle Configuration
- Click the **"⚙️ Settings"** button (gear icon, top right)
- Opens the **Advanced Settings** panel with:
  - Full vehicle configuration as editable JSON
  - Vehicle parameters: mass, thrust, ISP, burn times
  - Aerodynamics: drag coefficients, nose radius
  - Limits: max g-load, max heating
- Edit the JSON directly
- Click **"Save Configuration"**
  - System validates the new configuration
  - Rebuilds the reachability sweep (~10-30 seconds)
  - New configuration is saved to `vehicle_config.yaml`
  - You can now test trajectories with the updated vehicle
- Click **"Cancel"** to discard changes

#### 7. Clear Markers
- Click **"Clear Markers"** button to remove launch and landing points
- Start over with a new mission

### Interface Tips

- **Mobile-Friendly**: The interface works on tablets and phones (touch-friendly)
- **Example Missions**: Try these for feasible trajectories:
  - Cape Canaveral (28.5°N, -80.5°W) → Atlantic Ocean (35°N, -60°W): ~1500 km
  - Vandenberg (34.7°N, -120.6°W) → Pacific (40°N, -150°W): ~2500 km
- **Too Close**: Targets < ~400 km may be infeasible (below minimum range)
- **Too Far**: Targets > ~6000 km may be infeasible (beyond vehicle capability)
- **Constraint Violations**: The simulation enforces:
  - Peak g-load < 40 (default limit)
  - Peak stagnation heating < 1500 W/cm² (default limit)
- **Map Zoom**: Zoom in/out to find specific locations

---

## Using the REST API

The REST API is available for programmatic access. All endpoints return JSON.

### Interactive API Documentation

Visit **`http://localhost:8000/docs`** for interactive Swagger UI documentation with:
- Full endpoint descriptions
- Request/response schemas
- "Try it out" functionality to test endpoints

### Example API Calls (curl)

#### 1. Health Check

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "WARNING: NOTIONAL DEMO SERVICE - Results are for demonstration only"
}
```

#### 2. Get Vehicle Configuration

```bash
curl http://localhost:8000/api/config
```

**Response:**
```json
{
  "config": {
    "vehicle": {
      "name": "demo-vehicle-v0",
      "stages": [
        {
          "name": "stage_1",
          "mass_launch_kg": 6000,
          "mass_burnout_kg": 2200,
          "thrust_n": 180000,
          "isp_s": 265,
          "burn_time_s": 65
        },
        {
          "name": "stage_2",
          "mass_launch_kg": 2200,
          "mass_burnout_kg": 700,
          "thrust_n": 65000,
          "isp_s": 295,
          "burn_time_s": 65
        }
      ],
      ...
    },
    "aerodynamics": { ... },
    "limits": {
      "max_g_load": 40,
      "max_stagnation_heat_flux_w_cm2": 1500
    }
  },
  "warning": "All values are NOTIONAL DEMO PLACEHOLDERS only"
}
```

#### 3. Check Feasibility

```bash
curl -X POST http://localhost:8000/api/feasibility \
  -H "Content-Type: application/json" \
  -d '{
    "launch": {"lat": 28.5, "lon": -80.6},
    "landing": {"lat": 35.0, "lon": -60.0}
  }'
```

**Response (Feasible):**
```json
{
  "feasible": true,
  "range_km": 1523.7,
  "azimuth_deg": 62.3,
  "reasons": ["All constraints satisfied"],
  "distance_to_envelope_km": 234.5,
  "peak_g_load": 28.4,
  "peak_heat_flux_w_cm2": 987.2,
  "warning": "NOTIONAL DEMO RESULT - Not representative of any real system"
}
```

**Response (Infeasible - Too Far):**
```json
{
  "feasible": false,
  "range_km": 8234.1,
  "azimuth_deg": 45.0,
  "reasons": ["Range too far (8234.1 km > 6800.0 km maximum)"],
  "distance_to_envelope_km": 1434.1,
  "peak_g_load": null,
  "peak_heat_flux_w_cm2": null,
  "warning": "NOTIONAL DEMO RESULT - Not representative of any real system"
}
```

#### 4. Compute Full Trajectory

```bash
curl -X POST http://localhost:8000/api/trajectory \
  -H "Content-Type: application/json" \
  -d '{
    "launch": {"lat": 28.5, "lon": -80.6},
    "landing": {"lat": 35.0, "lon": -60.0}
  }'
```

**Response:** Same as feasibility, plus `trajectory` array with time-series data:
```json
{
  "feasible": true,
  "range_km": 1523.7,
  "azimuth_deg": 62.3,
  "reasons": ["All constraints satisfied"],
  "distance_to_envelope_km": 234.5,
  "peak_g_load": 28.4,
  "peak_heat_flux_w_cm2": 987.2,
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
    {
      "time_s": 1.0,
      "altitude_m": 123.4,
      "range_m": 87.2,
      ...
    },
    ...
  ],
  "warning": "NOTIONAL DEMO RESULT - Not representative of any real system"
}
```

#### 5. Update Vehicle Configuration

```bash
curl -X PUT http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle": {
      "name": "custom-vehicle",
      "stages": [ ... ],
      ...
    },
    "aerodynamics": { ... },
    "limits": { ... }
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Configuration updated and sweep rebuilt"
}
```

**Note:** Updating the configuration triggers a sweep rebuild (~10-30 seconds) and saves the new configuration to `vehicle_config.yaml`.

---

## Running Tests

This project includes comprehensive unit and integration tests.

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Files

```bash
# Test configuration loading
pytest tests/test_config.py -v

# Test atmosphere model
pytest tests/test_atmosphere.py -v

# Test simulation
pytest tests/test_simulation.py -v

# Test API endpoints
pytest tests/test_api.py -v

# Test authentication
pytest tests/test_auth.py -v
```

### Test Coverage

The test suite covers:
- ✅ Configuration loading and validation (YAML parsing, schema validation)
- ✅ Atmosphere model (US Standard 1976 density/pressure calculations)
- ✅ Sutton-Graves heating formula verification
- ✅ 3-DOF simulation execution (stage transitions, drag, gravity)
- ✅ Reachability sweep building and caching
- ✅ Feasibility checking (reachable, too far, g-limit, heating-limit)
- ✅ REST API endpoints (health, config, feasibility, trajectory)
- ✅ Password authentication (login, session management, protected routes)

---

## Railway Deployment (Production Hosting)

This repository is configured for one-command deployment to [Railway](https://railway.app), a modern hosting platform with automatic builds and HTTPS.

### Overview

- **What This PR Provides**: Full Railway deployment configuration
- **What This PR Does NOT Do**: Actually deploy a live service (configuration only)
- **Who Deploys**: The maintainer (John) can deploy later with one command
- **Estimated Cost**: $5-10/month on Railway Hobby plan for moderate traffic

### Prerequisites

- **Railway Account**: Sign up at [railway.app](https://railway.app) (free tier available)
- **GitHub Repository**: Repository must be pushed to GitHub
- **Basic Railway Knowledge**: Familiarity with Railway dashboard (optional but helpful)

### Step-by-Step Deployment

#### 1. Connect Repository to Railway

1. Log in to your [Railway dashboard](https://railway.app/dashboard)
2. Click **"New Project"** button
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account (first time only)
5. Select the `trajectory-generator` repository from the list
6. Railway will automatically:
   - Detect the `Dockerfile` in the repository
   - Read `railway.json` for deployment configuration
   - Begin the initial build (takes ~2-3 minutes)

#### 2. Configure Environment Variables

While the build is running, set up environment variables:

1. In the Railway project dashboard, click on your service
2. Go to the **"Variables"** tab
3. Add the following variables:

**Recommended Variables:**

| Variable | Value | Purpose |
|----------|-------|---------|
| `APP_PASSWORD` | `your_secure_password_here` | **Strongly recommended** for any public deployment. Protects the UI with password authentication. Use a strong password. |
| `CESIUM_ION_TOKEN` | `your_cesium_token` | **Optional** but recommended for better 3D imagery. Get a free token at [cesium.com/ion/signup](https://cesium.com/ion/signup). |

**Variables NOT to Set:**

| Variable | Why Not |
|----------|---------|
| `PORT` | Railway provides this automatically - do not override |
| `VEHICLE_CONFIG_PATH` | Uses default `/app/vehicle_config.yaml` from Docker - only set if using custom config mount |

**Example Configuration:**

```
APP_PASSWORD=Demo2024!Secure
CESIUM_ION_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

4. Click **"Add"** or save changes (auto-saved in Railway)

#### 3. Monitor the Build

1. Go to the **"Deployments"** tab
2. Watch the build logs in real-time:
   - ✅ Building Docker image
   - ✅ Installing Python dependencies
   - ✅ Copying application files
   - ✅ Starting uvicorn server
3. Wait for **"Build Successful"** and **"Deploy Successful"**

**Typical build time**: 2-3 minutes for first deployment, ~1-2 minutes for subsequent deploys.

#### 4. Generate a Public Domain

Railway deployments need a domain to be publicly accessible:

1. Go to the **"Settings"** tab in your Railway service
2. Scroll to the **"Networking"** section
3. Click **"Generate Domain"**
4. Railway will assign a URL like: `https://trajectory-generator-production-abc123.up.railway.app`
5. Copy this URL - this is your live service address

**Optional**: Add a custom domain (e.g., `demo.yourdomain.com`) by:
- Adding a CNAME record in your DNS provider pointing to the Railway domain
- Adding the custom domain in Railway's domain settings

#### 5. Verify the Deployment

Test your live service:

**1. Health Check:**
```bash
curl https://your-app.up.railway.app/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "WARNING: NOTIONAL DEMO SERVICE - Results are for demonstration only"
}
```

**2. Web Interface:**
- Visit `https://your-app.up.railway.app` in your browser
- If you set `APP_PASSWORD`, you'll see the login screen
- Enter your password and access the main interface
- Test a trajectory: Cape Canaveral → Atlantic Ocean

**3. API Documentation:**
- Visit `https://your-app.up.railway.app/docs` for Swagger UI

**4. Test a Feasibility Check:**
```bash
curl -X POST https://your-app.up.railway.app/api/feasibility \
  -H "Content-Type: application/json" \
  -d '{"launch": {"lat": 28.5, "lon": -80.6}, "landing": {"lat": 35.0, "lon": -60.0}}'
```

### Cost Estimation

**Railway Pricing** (as of October 2024):

| Plan | Cost | Included Resources | Best For |
|------|------|-------------------|----------|
| **Free Trial** | $5 credit (one-time) | 500 hours of compute | Initial testing |
| **Hobby** | $5/month | 500 hours ($0.01/hour) | Personal demos, prototypes |
| **Pro** | Pay-as-you-go | $0.01/hour + resources used | Production apps with traffic |

**Expected Usage for This Service:**

- **Service Class**: Small web service (~512 MB RAM, minimal CPU)
- **Compute**: Lightweight Python API, no heavy processing after initial startup
- **Storage**: Ephemeral only (sweep cache in memory, no persistent database)
- **Estimated Monthly Cost**: **$5-10 on Hobby plan** for moderate traffic (a few hundred requests/day)

**Cost Optimization Tips:**

- Railway automatically **sleeps your service when idle** (no traffic) - you only pay for active time
- No database or storage costs (sweep cache is in-memory)
- Initial sweep build takes ~10-30 seconds on cold start (cached afterward)
- Consider upgrading to Pro plan only if you consistently exceed 500 hours/month

### Railway Configuration Files

This repository includes three files for Railway deployment:

#### `Dockerfile` (Production-Ready Container)

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and static files
COPY src/ ./src/
COPY static/ ./static/
COPY vehicle_config.yaml .

ENV PYTHONPATH=/app/src
ENV PORT=8000

# Health check for Railway monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/health').read()" || exit 1

EXPOSE $PORT

# Run with PORT from Railway environment
CMD uvicorn trajgen.main:app --host 0.0.0.0 --port $PORT
```

**Key Features:**
- Binds to `0.0.0.0` (required for Railway external access)
- Honors Railway's `$PORT` environment variable
- Includes health check for Railway monitoring
- Copies all necessary files (code, static assets, config)

#### `railway.json` (Deployment Configuration)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3,
    "healthcheckPath": "/api/health",
    "healthcheckTimeout": 10
  }
}
```

**Configuration Details:**
- Uses Dockerfile builder (not Nixpacks)
- Single replica (suitable for demo workloads)
- Auto-restart on failure (up to 3 retries)
- Health check at `/api/health` every 10 seconds

#### `.env.example` (Environment Variable Template)

See "Configure Environment Variables" section above for usage.

### Troubleshooting Railway Deployment

#### Build Fails

**Symptoms**: Build logs show errors, deployment never completes

**Solutions**:
1. Check Python version: Must be 3.11+ in `Dockerfile`
2. Verify `requirements.txt` dependencies are compatible
3. Check Railway build logs for specific error messages
4. Ensure `Dockerfile` syntax is correct

#### Service Won't Start

**Symptoms**: Build succeeds but service crashes or becomes unhealthy

**Solutions**:
1. Check **Logs** tab in Railway for startup errors
2. Verify `/api/health` endpoint returns 200 OK:
   ```bash
   curl https://your-app.up.railway.app/api/health
   ```
3. Ensure `VEHICLE_CONFIG_PATH` is not set incorrectly (use default)
4. Check that `vehicle_config.yaml` is valid YAML
5. Look for Python tracebacks in logs indicating missing files or import errors

#### Performance Issues / Slow Response

**Symptoms**: UI is slow, API requests timeout

**Solutions**:
1. First request after idle period takes ~10-30 seconds (sweep rebuild) - this is normal
2. Check Railway **Metrics** tab for CPU/memory usage
3. Consider upgrading to a larger Railway plan if consistently hitting limits
4. Verify you're not rebuilding the sweep on every request (should be cached)

#### Authentication Not Working

**Symptoms**: Can't log in, or login screen doesn't appear

**Solutions**:
1. Verify `APP_PASSWORD` is set in Railway environment variables (not in code)
2. Try a different password (avoid special characters that might cause issues)
3. Clear browser cookies and try again
4. Check Railway logs for authentication errors

#### 3D View Not Loading / Black Globe

**Symptoms**: "View 3D" button opens blank screen, black globe, or shows errors

**Solutions**:
1. **Missing/Invalid Token**: The app now automatically falls back to OpenStreetMap imagery when `CESIUM_ION_TOKEN` is missing or invalid
   - You should see a notice: "📍 Using OpenStreetMap imagery (no Cesium Ion token)"
   - The globe will show OpenStreetMap tiles instead of satellite imagery
   - Trajectory, launch, and landing markers will still display correctly
2. **Token Rejected at Request Time**: If your token was valid initially but later expired or was revoked, the fallback will activate automatically
3. **To Use Ion Imagery**: Set a valid `CESIUM_ION_TOKEN` in Railway environment variables
   - Get a free token at [cesium.com/ion/signup](https://cesium.com/ion/signup)
   - After setting the token, redeploy or restart the service
4. Check browser console (F12) for specific Cesium errors if issues persist
5. Ensure HTTPS is enabled (Cesium requires secure context for Ion assets)

#### Deployment Not Auto-Updating

**Symptoms**: Pushed to `main` branch but Railway doesn't rebuild

**Solutions**:
1. Check Railway is connected to the correct GitHub repository
2. Verify Railway has permission to access your repository (check GitHub OAuth apps)
3. Go to **Deployments** tab and click **"Redeploy"** manually
4. Check Railway **Activity** feed for webhook failures

### Important Notes

- **This PR Does NOT Deploy**: This PR only adds configuration files. No live service is created by merging this PR.
- **Manual Deployment Required**: After merging, you must manually connect the repository to Railway to deploy.
- **Auto-Deploy from `main`**: After initial setup, Railway auto-deploys on every push to `main` branch.
- **NOTIONAL DEMO VALUES**: All simulation results remain notional placeholders, even in production.
- **HTTPS Included**: Railway automatically provides HTTPS for all deployments (no setup needed).

---

## Model Assumptions and Limitations

This simulator uses **simplified physics models** for educational purposes. Real trajectory simulation requires significantly more complexity.

### Simplifications

1. **Point Mass Model**: Vehicle treated as a single point with no attitude dynamics, rotation, or aerodynamic moments
2. **3-DOF (Three Degrees of Freedom)**: Motion only in vertical plane (range, altitude, velocity) - no lateral or cross-range motion
3. **Simplified Guidance**: Linear pitch program - real vehicles use closed-loop guidance (e.g., PEG, OPGUID)
4. **Gravity Turn**: After pitch-over, thrust vector aligns with velocity (zero angle of attack) - real vehicles actively control attitude
5. **Spherical Earth**: No oblateness (J2, J3, etc.), simple inverse-square gravity - real models use EGM2008 or WGS84
6. **Standard Atmosphere**: US Standard 1976 with no weather, wind, or density variations - real trajectories account for atmospheric uncertainty
7. **Fixed Azimuth**: Launch azimuth determined by great circle to target - real missions consider range safety, no-fly zones
8. **Simplified Heating**: Sutton-Graves stagnation point correlation only - real vehicles need full CFD and 3D heating distribution
9. **No Stage Dynamics**: Instantaneous stage separation with no rotation or tumbling
10. **No Dispersions**: Perfect execution with no navigation errors, thrust variations, or wind gusts

### Physics Models Used

| Physical Phenomenon | Model | Accuracy |
|---------------------|-------|----------|
| **Atmosphere** | US Standard Atmosphere 1976 (up to 85 km) | ±10-20% density variation from real atmosphere |
| **Drag** | Cd interpolated from Mach table, constant reference area | Approximate - real Cd varies with angle of attack |
| **Heating** | Sutton-Graves: q = 1.7415e-4 × sqrt(ρ/R_n) × v³ (SI) | Stagnation point only - no base or body heating |
| **Gravity** | Inverse-square: g = g₀ × (R_earth / r)² | No oblateness or higher-order terms |
| **Earth Rotation** | Simplified centrifugal effect | Approximate Coriolis and transport theorem neglected |

### Guidance Algorithm

The simulator uses a **simple linear pitch program** (not representative of real vehicles):

1. **0-20 km altitude**: Hold initial launch angle (vertical climb phase)
2. **20-80 km altitude**: Gradual pitch-down at 0.01 rad/s (pitch-over phase)
3. **Above 80 km**: Natural ballistic arc from gravity and centrifugal effects
4. Thrust always aligned with velocity vector (zero angle of attack assumption)

**Real vehicles** use sophisticated closed-loop guidance:
- Powered Explicit Guidance (PEG) for ascent
- Optimal trajectory shaping for constraints
- Real-time navigation updates
- Divert maneuvers for precision landing

### Feasibility Constraints

A trajectory is considered **feasible** if:

1. **Kinematically Reachable**: Within min/max range envelope from parameter sweep
2. **G-Load Limit**: Peak acceleration < `max_g_load` (default: 40 g's)
3. **Heating Limit**: Peak stagnation heat flux < `max_stagnation_heat_flux_w_cm2` (default: 1500 W/cm²)

**Real missions** have many more constraints:
- Range safety corridors
- No-fly zones
- Communication windows
- Landing site accessibility
- Weather conditions
- Propellant reserves

### Typical Demonstration Ranges

The default **notional vehicle parameters** are tuned for:

- **Minimum Range**: ~400 km (below this, may be kinematically infeasible)
- **Typical Range**: 1000-3000 km (ICBM-scale for map visualization)
- **Maximum Range**: ~6000 km (vehicle performance limit)

**Real vehicles** vary widely:
- Short-range tactical missiles: 100-500 km
- Medium-range ballistic missiles: 500-3000 km
- Intercontinental ballistic missiles: 5500-15,000 km
- Space launch vehicles: Orbit insertion (not ballistic return)

### When NOT to Use This Simulator

❌ **Do NOT use this simulator for:**

- Real mission planning or operational decisions
- Safety-critical analysis or certification
- Regulatory compliance or verification
- Performance validation of actual vehicles
- Engineering trade studies requiring high fidelity
- Academic research requiring peer-reviewed accuracy
- Any application where incorrect results could cause harm

✅ **Do use this simulator for:**

- Learning basic trajectory simulation concepts
- Prototyping user interfaces for mission planning tools
- Demonstrating API design for simulation services
- Educational examples in coursework or training
- Exploring parameter sensitivity (qualitatively)
- Building visualization and charting frontends

---

## Development

### Project Structure

```
trajectory-generator/
├── vehicle_config.yaml       # Vehicle configuration (YAML)
├── requirements.txt          # Python dependencies
├── Dockerfile               # Production Docker container
├── railway.json             # Railway deployment configuration
├── .env.example             # Environment variable template
├── .gitignore              # Git ignore rules
│
├── src/
│   └── trajgen/            # Main Python package
│       ├── __init__.py
│       ├── main.py         # Application entrypoint (uvicorn)
│       ├── api.py          # FastAPI endpoints + static file serving
│       ├── auth.py         # Password authentication middleware
│       ├── config.py       # Configuration loading and validation
│       ├── atmosphere.py   # US Standard Atmosphere 1976
│       ├── simulation.py   # 3-DOF trajectory simulation
│       ├── sweep.py        # Reachability sweep builder
│       └── feasibility.py  # Feasibility checker
│
├── static/                 # Web UI files (Phase 2)
│   ├── index.html         # Main application UI
│   ├── login.html         # Login page
│   ├── style.css          # Styling
│   └── app.js             # Client-side JavaScript
│
├── tests/                 # Test suite
│   ├── test_config.py     # Configuration tests
│   ├── test_atmosphere.py # Atmosphere model tests
│   ├── test_simulation.py # Simulation tests
│   ├── test_sweep.py      # Sweep tests
│   ├── test_feasibility.py # Feasibility tests
│   ├── test_api.py        # API endpoint tests
│   └── test_auth.py       # Authentication tests
│
└── .github/
    └── workflows/
        └── ci.yml         # GitHub Actions CI pipeline
```

### Phase Roadmap

**Phase 1** (Complete ✅):
- 3-DOF simulation engine
- Reachability sweep
- REST API endpoints
- Configuration system

**Phase 2** (Complete ✅):
- Interactive web UI with map
- Real-time feasibility and trajectory charts
- CesiumJS 3D visualization
- Password authentication
- Advanced settings editor

**Phase 3** (This PR ✅):
- Railway deployment configuration
- Production-ready Docker container
- Environment variable documentation
- Deployment guide
- **Note**: Configuration only - no live service deployed

**Phase 4** (Future):
- Actual production deployment (by maintainer)
- Monitoring and logging enhancements
- Performance optimizations
- Extended documentation

---

## Frequently Asked Questions

### Q: Why are all the parameters "notional demo values"?

**A:** This is an educational demonstration project, not a real engineering tool. The vehicle parameters, simulation results, and constraint limits are illustrative placeholders chosen to produce reasonable-looking trajectories for demonstration purposes. They do not represent any actual vehicle, system, or operational capability.

### Q: Can I use this for my school project?

**A:** Yes, with caveats. This is suitable for **learning concepts** and **prototyping interfaces**, but be clear in your report that:
- The physics models are simplified (3-DOF, point mass)
- The parameters are notional (not validated against real data)
- The results are for demonstration only (not suitable for analysis)

For academic work requiring validated results, use industry-standard tools like GMAT, STK, or OTIS.

### Q: How accurate is the simulation?

**A:** **Not very accurate** compared to professional trajectory simulators. This is a simplified 3-DOF point-mass model with standard atmosphere and basic heating. Real trajectory simulation requires:
- 6-DOF dynamics (attitude, rotation, aerodynamic moments)
- High-fidelity atmosphere models (wind, density variations)
- Closed-loop guidance algorithms (PEG, OPGUID)
- Full aerodynamic database (Cd, Cl, Cm vs Mach/alpha)
- Detailed thermal models (3D heating distribution)
- Navigation and sensor models (GPS, IMU, radar)

**This simulator is suitable for educational demonstrations only.**

### Q: Can I change the vehicle configuration?

**A:** Yes! Edit `vehicle_config.yaml` or use the **Advanced Settings** in the web UI. You can adjust:
- Stage masses, thrust, ISP, burn times
- Drag coefficients vs Mach
- Nose radius (affects heating)
- G-load and heating limits

The system validates your configuration and rebuilds the reachability sweep automatically.

### Q: Why do some trajectories show as infeasible?

**A:** A trajectory is infeasible if it violates any of these constraints:
1. **Too Far**: Beyond the vehicle's maximum range (~6000 km for default config)
2. **Too Close**: Below minimum range (~400 km for default config)
3. **G-Load Violation**: Peak acceleration exceeds limit (default: 40 g's)
4. **Heating Violation**: Peak stagnation heat flux exceeds limit (default: 1500 W/cm²)

Try adjusting the landing point or modifying the vehicle configuration to relax limits.

### Q: What does the "distance to envelope" mean?

**A:** This is the distance (in km) from the requested trajectory to the boundary of the reachability envelope. A **positive** distance means the trajectory is inside the feasible region (good). A **negative** distance means it's outside (infeasible). This gives you a sense of how much margin you have.

### Q: Why is the sweep rebuild so slow?

**A:** The reachability sweep performs a parameter sweep over launch angles and burn parameters, simulating hundreds of trajectories to build the feasibility envelope. This takes ~10-30 seconds depending on your CPU. The sweep is **cached** to `.cache/sweep_cache.json` and only rebuilt when you change the vehicle configuration.

### Q: Does this support multiple users?

**A:** The **authentication system** is designed for **single-user demo deployments**. It uses simple password authentication (one password for the entire deployment). This is suitable for personal demos, prototypes, or classroom demonstrations.

For multi-user production applications, you would need to implement:
- User database with per-user credentials
- Proper session management with secure storage
- HTTPS enforcement
- Password hashing (bcrypt, argon2)
- Rate limiting and CSRF protection

### Q: Can I use this with Docker locally?

**A:** Yes! Build and run the Docker container:

```bash
# Build the image
docker build -t trajectory-generator .

# Run the container
docker run -p 8000:8000 \
  -e APP_PASSWORD=demo123 \
  -e CESIUM_ION_TOKEN=your_token \
  trajectory-generator
```

Then visit `http://localhost:8000` in your browser.

### Q: How do I get a Cesium Ion token?

**A:**
1. Go to [cesium.com/ion/signup](https://cesium.com/ion/signup)
2. Sign up for a free account
3. Go to **Access Tokens** in your dashboard
4. Create a new token or use the default token
5. Copy the token and set as `CESIUM_ION_TOKEN` environment variable

The **default token** works but may have rate limits. Your personal token provides better imagery and higher quotas.

### Q: My `.env` file isn't being loaded / Cesium token not working

**A:** If you've created a `.env` file but the values aren't being picked up:

1. **Check file location**: The `.env` file must be in the **project root** (same directory as `vehicle_config.yaml` and `requirements.txt`), not in `src/` or any subdirectory.

2. **Check file format**: 
   - Use simple `KEY=value` format (one per line)
   - No spaces around the `=` sign: use `CESIUM_ION_TOKEN=abc123`, not `CESIUM_ION_TOKEN = abc123`
   - Don't use quotes unless the value itself contains quotes
   - Comments start with `#`

3. **Verify the token in the API response**:
   ```bash
   curl http://localhost:8000/api/cesium-token
   ```
   This should return `{"token": "your_token", "has_token": true}` if loaded correctly.

4. **Check for typos**: Variable names are case-sensitive. Use `CESIUM_ION_TOKEN` (not `cesium_ion_token` or `CesiumIonToken`).

5. **Restart the service**: Changes to `.env` are only loaded when the service starts. After editing `.env`, restart the server:
   - Press `Ctrl+C` to stop
   - Run `python -m src.trajgen.main` again

6. **Check for whitespace/quotes**: 
   - ✅ Correct: `CESIUM_ION_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
   - ❌ Wrong: `CESIUM_ION_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`
   - ❌ Wrong: `CESIUM_ION_TOKEN= eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (leading space)

7. **Environment variables take precedence**: If you previously exported the variable in your shell (`export CESIUM_ION_TOKEN=...`), that value will be used instead of the `.env` file. Unset it with `unset CESIUM_ION_TOKEN` or start a fresh terminal.

8. **Check Railway deployment**: On Railway, environment variables are set through the Railway dashboard (Variables tab), **not** through a `.env` file. The `.env` file is only for local development.

---

## License

This is a demonstration project. See repository license for details.

---

## Contributing

Contributions are welcome! Please remember:

- All vehicle parameters and results are **notional placeholders for demonstration only**
- The simulation is **simplified** (3-DOF point-mass) and not suitable for real analysis
- Keep the **NOTIONAL DEMO VALUES disclaimer** prominent in all changes
- Add tests for new features
- Update documentation for any API or configuration changes

---

## Contact

For questions, issues, or suggestions, please open a GitHub issue in the repository.

**Remember**: This is a demonstration service. All values are notional. Do not use for real mission planning or operational decisions.
