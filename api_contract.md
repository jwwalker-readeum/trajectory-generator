# API Contract Documentation

**NOTIONAL DEMO SERVICE** - All simulation results are for demonstration only.

This document defines the contract between the frontend (`static/app.js`) and backend API (`src/trajgen/api.py`).

## Critical: Coordinate Normalization

**Frontend must normalize coordinates before sending:**
- Longitude: Use `latlng.wrap()` to ensure [-180, 180] range (Leaflet can return values outside this on wrapped maps)
- Latitude: Clamp to [-90, 90]

**Backend validates:**
- Rejects lat outside [-90, 90] with 422
- Rejects lon outside [-180, 180] with 422

## API Endpoints

### POST /api/feasibility

Check if a launch-landing pair is feasible without computing the full trajectory.

**Request Body:**
```typescript
{
  launch: {
    lat: number,  // Latitude in degrees, -90 to 90
    lon: number   // Longitude in degrees, -180 to 180
  },
  landing: {
    lat: number,  // Latitude in degrees, -90 to 90
    lon: number   // Longitude in degrees, -180 to 180
  }
}
```

**Response (200 OK):**
```typescript
{
  feasible: boolean,                    // Whether the trajectory is feasible
  range_km: number,                     // Great circle distance
  azimuth_deg: number,                  // Launch azimuth
  reasons: string[],                    // List of constraint check results
  distance_to_envelope_km: number,      // Distance to envelope boundary
  peak_g_load: number | null,          // Peak g-load (null if not computed)
  peak_heat_flux_w_cm2: number | null, // Peak heat flux (null if not computed)
  warning: string                       // NOTIONAL DEMO warning message
}
```

**Frontend Usage:**
- `static/app.js` lines 240-270 (checkFeasibility function)
- Displays `feasible`, `reasons`, `peak_g_load`, `peak_heat_flux_w_cm2`, `distance_to_envelope_km`
- Lines 319-344 (displayFeasibilityResult function)

**Validation Errors (422):**
- Latitude out of range [-90, 90]
- Longitude out of range [-180, 180]
- Missing required fields
- Invalid data types

---

### POST /api/trajectory

Compute the full trajectory for a launch-landing pair.

**Request Body:**
```typescript
{
  launch: {
    lat: number,  // Latitude in degrees, -90 to 90
    lon: number   // Longitude in degrees, -180 to 180
  },
  landing: {
    lat: number,  // Latitude in degrees, -90 to 90
    lon: number   // Longitude in degrees, -180 to 180
  }
}
```

**Response (200 OK):**
```typescript
{
  feasible: boolean,
  range_km: number,
  azimuth_deg: number,
  reasons: string[],
  distance_to_envelope_km: number,
  peak_g_load: number | null,
  peak_heat_flux_w_cm2: number | null,
  trajectory: TrajectoryPoint[] | null,  // null if infeasible
  warning: string
}
```

**TrajectoryPoint Structure:**
```typescript
{
  time_s: number,                     // Time since launch (seconds)
  altitude_m: number,                 // Altitude (meters)
  range_m: number,                    // Downrange distance (meters)
  velocity_m_s: number,               // Velocity magnitude (m/s)
  mach: number,                       // Mach number
  g_load: number,                     // G-load experienced
  heat_flux_w_cm2: number,           // Heat flux (W/cm²)
  latitude_deg: number,               // Current latitude
  longitude_deg: number,              // Current longitude
  flight_path_angle_deg: number,     // Flight path angle
  phase: string                       // Flight phase
}
```

**Frontend Usage:**
- `static/app.js` lines 272-310 (computeTrajectory function)
- Charts use: `time_s`, `range_m`, `altitude_m`, `mach` (lines 348-530)
- 3D visualization uses: `latitude_deg`, `longitude_deg`, `altitude_m` (lines 607-690)

**Required Trajectory Fields for Frontend:**
- `time_s` - Used in altitude vs time and Mach vs time charts
- `range_m` - Used in altitude vs range chart
- `altitude_m` - Used in all charts and 3D visualization
- `mach` - Used in Mach vs time chart
- `latitude_deg` - Used in 3D visualization (CesiumJS)
- `longitude_deg` - Used in 3D visualization (CesiumJS)

---

### GET /api/config

Get the current vehicle configuration.

**Response (200 OK):**
```typescript
{
  config: {
    vehicle: {
      mass_kg: number,
      reference_area_m2: number,
      nose_radius_m: number
    },
    aerodynamics: {
      cl_alpha: number,
      cd0: number,
      k_induced: number
    },
    limits: {
      max_g_load: number,
      max_stagnation_heat_flux_w_cm2: number,
      max_dynamic_pressure_pa: number
    },
    environment: {
      atmosphere_model: string
    },
    sweep: {
      launch_angle_min_deg: number,
      launch_angle_max_deg: number,
      launch_angle_step_deg: number,
      burn_param_min: number,
      burn_param_max: number,
      burn_param_step: number
    }
  },
  warning: string
}
```

**Frontend Usage:**
- `static/app.js` lines 694-703 (loadConfigForEditor)
- Displayed in settings modal as JSON editor

---

### PUT /api/config

Update the vehicle configuration and rebuild the sweep.

**Request Body:**
```typescript
{
  // Same structure as the 'config' field from GET /api/config
  vehicle: { ... },
  aerodynamics: { ... },
  limits: { ... },
  environment: { ... },
  sweep: { ... }
}
```

**Response (200 OK):**
```typescript
{
  status: string,
  message: string
}
```

**Error Response (400 Bad Request):**
```typescript
{
  detail: string  // Validation error message
}
```

**Frontend Usage:**
- `static/app.js` lines 736-784 (saveConfig function)

---

### GET /api/cesium-token

Get the Cesium Ion access token for 3D terrain.

**Response (200 OK):**
```typescript
{
  token: string | null,    // Ion token or null if not configured
  has_token: boolean       // Whether a valid token is available
}
```

**Frontend Usage:**
- `static/app.js` lines 556-578 (initializeCesium function)
- Uses token to load Cesium Ion terrain

---

## Testing

Run UI contract tests:
```bash
pytest tests/test_ui_contract.py -v
```

Tests verify the exact payload format sent by the frontend matches API expectations.

## Common 422 Validation Errors

1. **Longitude out of range** - Leaflet returns lon outside [-180, 180] on wrapped maps (FIXED: frontend now normalizes)
2. **Missing Content-Type** - Must be `application/json`
3. **Invalid coordinates** - lat must be [-90, 90], lon must be [-180, 180]
4. **Missing fields** - Both `launch` and `landing` with `lat` and `lon` required

Frontend now shows specific validation errors instead of generic "Failed to check feasibility" message.
