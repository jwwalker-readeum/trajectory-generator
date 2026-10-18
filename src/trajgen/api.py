"""FastAPI application for trajectory generation service.

NOTIONAL DEMO SERVICE - All simulation results are for demonstration only.
"""

from fastapi import FastAPI, HTTPException, status, Form
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from pathlib import Path

from .config import VehicleConfig, ConfigError
from .sweep import ReachabilitySweep
from .feasibility import FeasibilityChecker
from .auth import PasswordAuthMiddleware, get_required_password, verify_session_token, generate_session_token


# Global state
app_state = {
    'config': None,
    'sweep': None,
    'checker': None
}


class LatLon(BaseModel):
    """Latitude and longitude with defensive coordinate normalization.
    
    Frontend should normalize coordinates, but we also wrap server-side
    to handle edge cases (e.g., clicks on wrapped Leaflet world copies).
    """
    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lon: float = Field(..., description="Longitude in degrees (will be wrapped to [-180, 180])")
    
    @field_validator('lon', mode='before')
    @classmethod
    def wrap_longitude(cls, v: float) -> float:
        """Wrap longitude to [-180, 180] range before validation.
        
        This handles cases where Leaflet returns coordinates outside the standard
        range when users click on wrapped copies of the world map.
        
        Examples:
            -215.419922 -> 144.580078
            -236.953125 -> 123.046875
            400.0 -> 40.0
        """
        # Wrap to [-180, 180] range
        while v > 180:
            v -= 360
        while v < -180:
            v += 360
        return v


class FeasibilityRequest(BaseModel):
    """Request for feasibility check."""
    launch: LatLon
    landing: LatLon


class TrajectoryRequest(BaseModel):
    """Request for trajectory computation."""
    launch: LatLon
    landing: LatLon


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup: load config and build sweep
    print("Initializing trajectory generation service...")
    print("WARNING: All vehicle parameters and results are NOTIONAL DEMO VALUES ONLY")
    
    try:
        config = VehicleConfig()
        sweep = ReachabilitySweep(config)
        sweep.load_or_build()
        checker = FeasibilityChecker(config, sweep)
        
        app_state['config'] = config
        app_state['sweep'] = sweep
        app_state['checker'] = checker
        
        print("Service initialized successfully")
    except Exception as e:
        print(f"ERROR: Failed to initialize service: {e}")
        raise
    
    yield
    
    # Shutdown
    print("Shutting down trajectory generation service")


app = FastAPI(
    title="Demo Trajectory Generator",
    description="NOTIONAL DEMO SERVICE - All results are for demonstration only",
    version="0.1.0",
    lifespan=lifespan
)

# Add password authentication middleware
app.add_middleware(PasswordAuthMiddleware)

# Mount static files (HTML, CSS, JS)
static_dir = Path(__file__).parent.parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Redirect to main UI."""
    return RedirectResponse(url="/static/index.html")


@app.post("/api/login")
async def login(password: str = Form(...)) -> Dict[str, Any]:
    """Login endpoint for password authentication."""
    required_password = get_required_password()
    
    # If no password configured, allow access
    if required_password is None:
        return {"success": True, "message": "Authentication disabled"}
    
    # Check password
    import secrets
    if secrets.compare_digest(password, required_password):
        token = generate_session_token(password)
        response = JSONResponse({
            "success": True,
            "message": "Login successful"
        })
        response.set_cookie(
            key='session_token',
            value=token,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite='lax'
        )
        return response
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )


@app.get("/api/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    if app_state['config'] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    return {
        "status": "healthy",
        "message": "WARNING: NOTIONAL DEMO SERVICE - Results are for demonstration only"
    }


@app.get("/api/cesium-token")
async def get_cesium_token() -> Dict[str, Any]:
    """Get Cesium Ion token from environment.
    
    Returns the token if set, or null if not configured.
    """
    import os
    token = os.environ.get('CESIUM_ION_TOKEN', None)
    
    # Don't expose the placeholder value
    if token == 'YOUR_ION_TOKEN_HERE':
        token = None
    
    return {
        "token": token,
        "has_token": token is not None
    }


@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    """Get current vehicle configuration."""
    if app_state['config'] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    
    return {
        "config": app_state['config'].to_dict(),
        "warning": "All values are NOTIONAL DEMO PLACEHOLDERS only"
    }


@app.put("/api/config")
async def update_config(config_data: Dict[str, Any]) -> Dict[str, str]:
    """Update vehicle configuration.
    
    This will validate, save, and trigger a sweep rebuild.
    """
    if app_state['config'] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    
    try:
        # Save and reload config
        app_state['config'].save(config_data)
        
        # Rebuild sweep with new config
        print("Config updated, rebuilding sweep...")
        app_state['sweep'] = ReachabilitySweep(app_state['config'])
        app_state['sweep'].build()
        
        # Update checker
        app_state['checker'] = FeasibilityChecker(app_state['config'], app_state['sweep'])
        
        return {
            "status": "success",
            "message": "Configuration updated and sweep rebuilt"
        }
    
    except ConfigError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration validation error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@app.post("/api/feasibility")
async def check_feasibility(request: FeasibilityRequest) -> Dict[str, Any]:
    """Check feasibility of launch-landing pair.
    
    Returns feasibility status, constraints, and envelope information.
    """
    if app_state['checker'] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    
    try:
        result = app_state['checker'].check_feasibility(
            launch_lat=request.launch.lat,
            launch_lon=request.launch.lon,
            landing_lat=request.landing.lat,
            landing_lon=request.landing.lon,
            compute_trajectory=False
        )
        
        return {
            "feasible": result.feasible,
            "range_km": result.range_km,
            "azimuth_deg": result.azimuth_deg,
            "reasons": result.reasons,
            "distance_to_envelope_km": result.distance_to_envelope_km,
            "peak_g_load": result.peak_g_load,
            "peak_heat_flux_w_cm2": result.peak_heat_flux_w_cm2,
            "warning": "NOTIONAL DEMO RESULT - Not representative of any real system"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feasibility check failed: {str(e)}"
        )


@app.post("/api/trajectory")
async def compute_trajectory(request: TrajectoryRequest) -> Dict[str, Any]:
    """Compute full trajectory for launch-landing pair.
    
    Returns feasibility plus time-series trajectory data if feasible.
    """
    if app_state['checker'] is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service not initialized"
        )
    
    try:
        result = app_state['checker'].check_feasibility(
            launch_lat=request.launch.lat,
            launch_lon=request.launch.lon,
            landing_lat=request.landing.lat,
            landing_lon=request.landing.lon,
            compute_trajectory=True
        )
        
        response = {
            "feasible": result.feasible,
            "range_km": result.range_km,
            "azimuth_deg": result.azimuth_deg,
            "reasons": result.reasons,
            "distance_to_envelope_km": result.distance_to_envelope_km,
            "peak_g_load": result.peak_g_load,
            "peak_heat_flux_w_cm2": result.peak_heat_flux_w_cm2,
            "trajectory": result.trajectory if result.feasible else None,
            "warning": "NOTIONAL DEMO RESULT - Not representative of any real system"
        }
        
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trajectory computation failed: {str(e)}"
        )
