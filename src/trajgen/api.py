"""FastAPI application for trajectory generation service.

NOTIONAL DEMO SERVICE - All simulation results are for demonstration only.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from .config import VehicleConfig, ConfigError
from .sweep import ReachabilitySweep
from .feasibility import FeasibilityChecker


# Global state
app_state = {
    'config': None,
    'sweep': None,
    'checker': None
}


class LatLon(BaseModel):
    """Latitude and longitude."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in degrees")


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
