// Demo Trajectory Generator - Main Application
// NOTIONAL DEMO - All simulation results are for demonstration only

// Application State
const state = {
    map: null,
    launchMarker: null,
    landingMarker: null,
    trajectoryLine: null,
    launch: null,
    landing: null,
    lastFeasibilityResult: null,
    lastTrajectory: null,
    altitudeRangeChart: null,
    altitudeTimeChart: null,
    machTimeChart: null,
    cesiumViewer: null,
    currentConfig: null
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    initializeEventListeners();
    loadConfigForEditor();
});

// Initialize Leaflet Map
function initializeMap() {
    // Create map centered on mid-latitudes
    state.map = L.map('map').setView([35.0, -10.0], 3);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(state.map);
    
    // Handle map clicks
    state.map.on('click', handleMapClick);
}

// Handle map click for setting launch/landing points
function handleMapClick(e) {
    const { lat, lng } = e.latlng;
    
    if (!state.launch) {
        // Set launch point
        setLaunch(lat, lng);
    } else if (!state.landing) {
        // Set landing point
        setLanding(lat, lng);
    } else {
        // Reset and set new launch
        clearMarkers();
        setLaunch(lat, lng);
    }
}

// Set launch point
function setLaunch(lat, lon) {
    state.launch = { lat, lon };
    
    if (state.launchMarker) {
        state.map.removeLayer(state.launchMarker);
    }
    
    const icon = L.divIcon({
        className: 'launch-marker',
        html: '<div style="background: #3b82f6; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">🚀</div>',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });
    
    state.launchMarker = L.marker([lat, lon], { icon }).addTo(state.map);
    
    updateInfoDisplay();
    updateButtons();
}

// Set landing point
function setLanding(lat, lon) {
    state.landing = { lat, lon };
    
    if (state.landingMarker) {
        state.map.removeLayer(state.landingMarker);
    }
    
    const icon = L.divIcon({
        className: 'landing-marker',
        html: '<div style="background: #ef4444; color: white; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">🎯</div>',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });
    
    state.landingMarker = L.marker([lat, lon], { icon }).addTo(state.map);
    
    // Draw line between launch and landing
    if (state.trajectoryLine) {
        state.map.removeLayer(state.trajectoryLine);
    }
    
    state.trajectoryLine = L.polyline([
        [state.launch.lat, state.launch.lon],
        [state.landing.lat, state.landing.lon]
    ], {
        color: '#8b5cf6',
        weight: 3,
        dashArray: '10, 10',
        opacity: 0.7
    }).addTo(state.map);
    
    // Fit bounds to show both markers
    const bounds = L.latLngBounds([
        [state.launch.lat, state.launch.lon],
        [state.landing.lat, state.landing.lon]
    ]);
    state.map.fitBounds(bounds, { padding: [50, 50] });
    
    updateInfoDisplay();
    updateButtons();
}

// Clear all markers
function clearMarkers() {
    if (state.launchMarker) {
        state.map.removeLayer(state.launchMarker);
        state.launchMarker = null;
    }
    if (state.landingMarker) {
        state.map.removeLayer(state.landingMarker);
        state.landingMarker = null;
    }
    if (state.trajectoryLine) {
        state.map.removeLayer(state.trajectoryLine);
        state.trajectoryLine = null;
    }
    
    state.launch = null;
    state.landing = null;
    state.lastFeasibilityResult = null;
    state.lastTrajectory = null;
    
    updateInfoDisplay();
    updateButtons();
    showEmptyState();
}

// Update info display
function updateInfoDisplay() {
    const launchInfo = document.getElementById('launchInfo');
    const landingInfo = document.getElementById('landingInfo');
    const rangeInfo = document.getElementById('rangeInfo');
    const feasibilityInfo = document.getElementById('feasibilityInfo');
    
    if (state.launch) {
        launchInfo.textContent = `${state.launch.lat.toFixed(3)}°, ${state.launch.lon.toFixed(3)}°`;
    } else {
        launchInfo.textContent = 'Click map to set';
    }
    
    if (state.landing) {
        landingInfo.textContent = `${state.landing.lat.toFixed(3)}°, ${state.landing.lon.toFixed(3)}°`;
        
        // Calculate great circle distance
        const range = calculateGreatCircleDistance(
            state.launch.lat, state.launch.lon,
            state.landing.lat, state.landing.lon
        );
        rangeInfo.textContent = `${range.toFixed(1)} km`;
    } else {
        landingInfo.textContent = 'Not set';
        rangeInfo.textContent = '-';
    }
    
    if (state.lastFeasibilityResult) {
        feasibilityInfo.textContent = state.lastFeasibilityResult.feasible ? '✓ Feasible' : '✗ Infeasible';
        feasibilityInfo.className = state.lastFeasibilityResult.feasible ? 'info-value status-feasible' : 'info-value status-infeasible';
    } else {
        feasibilityInfo.textContent = 'Unknown';
        feasibilityInfo.className = 'info-value status-unknown';
    }
}

// Update button states
function updateButtons() {
    const checkBtn = document.getElementById('checkFeasibilityBtn');
    const computeBtn = document.getElementById('computeTrajectoryBtn');
    
    const canCheck = state.launch && state.landing;
    checkBtn.disabled = !canCheck;
    computeBtn.disabled = !canCheck;
}

// Calculate great circle distance using Haversine formula
function calculateGreatCircleDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

// Initialize event listeners
function initializeEventListeners() {
    document.getElementById('clearBtn').addEventListener('click', clearMarkers);
    document.getElementById('checkFeasibilityBtn').addEventListener('click', checkFeasibility);
    document.getElementById('computeTrajectoryBtn').addEventListener('click', computeTrajectory);
    document.getElementById('settingsBtn').addEventListener('click', openSettingsModal);
    document.getElementById('aboutBtn').addEventListener('click', openAboutModal);
    document.getElementById('show3DBtn').addEventListener('click', show3DVisualization);
    
    // Modal close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.modal').classList.remove('show');
        });
    });
    
    // Close modal on outside click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    });
    
    // Config editor buttons
    document.getElementById('cancelConfigBtn').addEventListener('click', () => {
        document.getElementById('settingsModal').classList.remove('show');
    });
    document.getElementById('saveConfigBtn').addEventListener('click', saveConfig);
}

// Check feasibility
async function checkFeasibility() {
    if (!state.launch || !state.landing) return;
    
    showLoading('Checking feasibility...');
    
    try {
        const response = await fetch('/api/feasibility', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                launch: state.launch,
                landing: state.landing
            })
        });
        
        if (!response.ok) {
            throw new Error('Feasibility check failed');
        }
        
        const result = await response.json();
        state.lastFeasibilityResult = result;
        
        displayFeasibilityResult(result);
        updateInfoDisplay();
    } catch (error) {
        console.error('Error checking feasibility:', error);
        alert('Failed to check feasibility. Please try again.');
    } finally {
        hideLoading();
    }
}

// Compute trajectory
async function computeTrajectory() {
    if (!state.launch || !state.landing) return;
    
    showLoading('Computing trajectory...');
    
    try {
        const response = await fetch('/api/trajectory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                launch: state.launch,
                landing: state.landing
            })
        });
        
        if (!response.ok) {
            throw new Error('Trajectory computation failed');
        }
        
        const result = await response.json();
        state.lastFeasibilityResult = result;
        state.lastTrajectory = result.trajectory;
        
        displayFeasibilityResult(result);
        
        if (result.feasible && result.trajectory) {
            displayTrajectoryCharts(result.trajectory);
            document.getElementById('show3DBtn').style.display = 'block';
        }
        
        updateInfoDisplay();
    } catch (error) {
        console.error('Error computing trajectory:', error);
        alert('Failed to compute trajectory. Please try again.');
    } finally {
        hideLoading();
    }
}

// Display feasibility result
function displayFeasibilityResult(result) {
    document.getElementById('emptyState').style.display = 'none';
    document.getElementById('resultsContent').style.display = 'block';
    
    // Update constraint values
    document.getElementById('gLoadValue').textContent = 
        result.peak_g_load ? `${result.peak_g_load.toFixed(1)} G` : 'N/A';
    document.getElementById('heatFluxValue').textContent = 
        result.peak_heat_flux_w_cm2 ? `${result.peak_heat_flux_w_cm2.toFixed(0)} W/cm²` : 'N/A';
    document.getElementById('envelopeDistance').textContent = 
        result.distance_to_envelope_km ? `${result.distance_to_envelope_km.toFixed(1)} km` : 'N/A';
    
    // Display reasons
    const reasonsList = document.getElementById('reasonsList');
    reasonsList.innerHTML = '';
    
    if (result.reasons && result.reasons.length > 0) {
        result.reasons.forEach(reason => {
            const div = document.createElement('div');
            div.className = 'reason-item';
            
            if (result.feasible) {
                div.classList.add('reason-success');
            } else if (reason.toLowerCase().includes('limit') || reason.toLowerCase().includes('exceed')) {
                div.classList.add('reason-error');
            } else {
                div.classList.add('reason-warning');
            }
            
            div.textContent = reason;
            reasonsList.appendChild(div);
        });
    }
}

// Display trajectory charts
function displayTrajectoryCharts(trajectory) {
    if (!trajectory || trajectory.length === 0) return;
    
    // Prepare data
    const rangeData = trajectory.map(p => ({
        x: p.range_m / 1000, // Convert to km
        y: p.altitude_m / 1000 // Convert to km
    }));
    
    const altitudeTimeData = trajectory.map(p => ({
        x: p.time_s,
        y: p.altitude_m / 1000 // Convert to km
    }));
    
    const machTimeData = trajectory.map(p => ({
        x: p.time_s,
        y: p.mach
    }));
    
    // Altitude vs Range Chart
    const altRangeCtx = document.getElementById('altitudeRangeChart').getContext('2d');
    
    if (state.altitudeRangeChart) {
        state.altitudeRangeChart.destroy();
    }
    
    state.altitudeRangeChart = new Chart(altRangeCtx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Trajectory',
                data: rangeData,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `Alt: ${context.parsed.y.toFixed(1)} km, Range: ${context.parsed.x.toFixed(1)} km`
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Range (km)'
                    }
                },
                y: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Altitude (km)'
                    },
                    beginAtZero: true
                }
            }
        }
    });
    
    // Altitude vs Time Chart
    const altTimeCtx = document.getElementById('altitudeTimeChart').getContext('2d');
    
    if (state.altitudeTimeChart) {
        state.altitudeTimeChart.destroy();
    }
    
    state.altitudeTimeChart = new Chart(altTimeCtx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Altitude',
                data: altitudeTimeData,
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `Alt: ${context.parsed.y.toFixed(1)} km, Time: ${context.parsed.x.toFixed(1)} s`
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Time (s)'
                    },
                    beginAtZero: true
                },
                y: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Altitude (km)'
                    },
                    beginAtZero: true
                }
            }
        }
    });
    
    // Mach vs Time Chart
    const machTimeCtx = document.getElementById('machTimeChart').getContext('2d');
    
    if (state.machTimeChart) {
        state.machTimeChart.destroy();
    }
    
    state.machTimeChart = new Chart(machTimeCtx, {
        type: 'line',
        data: {
            datasets: [{
                label: 'Mach Number',
                data: machTimeData,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (context) => `Mach: ${context.parsed.y.toFixed(2)}, Time: ${context.parsed.x.toFixed(1)} s`
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Time (s)'
                    },
                    beginAtZero: true
                },
                y: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Mach Number'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

// Show 3D Visualization
async function show3DVisualization() {
    if (!state.lastTrajectory || state.lastTrajectory.length === 0) {
        alert('No trajectory data available');
        return;
    }
    
    const modal = document.getElementById('cesiumModal');
    modal.classList.add('show');
    
    // Initialize Cesium if not already done
    if (!state.cesiumViewer) {
        await initializeCesium();
    }
    
    // Update trajectory
    displayTrajectoryInCesium(state.lastTrajectory);
}

// Initialize CesiumJS viewer
async function initializeCesium() {
    const container = document.getElementById('cesiumContainer');
    let usingFallback = false;
    
    try {
        // Fetch Cesium Ion token from server
        const tokenResponse = await fetch('/api/cesium-token');
        const tokenData = await tokenResponse.json();
        
        let terrainProvider;
        let imageryProvider;
        
        if (tokenData.has_token && tokenData.token) {
            // Token available - try to use Ion assets
            Cesium.Ion.defaultAccessToken = tokenData.token;
            
            try {
                // Try to use world terrain with Ion
                terrainProvider = await Cesium.createWorldTerrainAsync();
                // If terrain succeeds, try Ion imagery (Bing Maps)
                // Default Cesium imagery will be used automatically if we don't set imageryProvider
                // We'll validate by creating a test viewer first
                imageryProvider = undefined; // Use Cesium default (Ion Bing Maps)
            } catch (ionError) {
                console.warn('Failed to load Ion assets (invalid or expired token), falling back to free resources:', ionError);
                usingFallback = true;
                terrainProvider = new Cesium.EllipsoidTerrainProvider();
                imageryProvider = new Cesium.OpenStreetMapImageryProvider({
                    url: 'https://a.tile.openstreetmap.org/'
                });
            }
        } else {
            // No token - use free resources
            console.info('No Cesium Ion token configured, using free OpenStreetMap imagery and basic terrain');
            usingFallback = true;
            terrainProvider = new Cesium.EllipsoidTerrainProvider();
            imageryProvider = new Cesium.OpenStreetMapImageryProvider({
                url: 'https://a.tile.openstreetmap.org/'
            });
        }
        
        // Create viewer with configured providers
        const viewerOptions = {
            terrainProvider: terrainProvider,
            baseLayerPicker: false,
            geocoder: false,
            homeButton: true,
            sceneModePicker: true,
            navigationHelpButton: false,
            animation: false,
            timeline: false,
            fullscreenButton: false
        };
        
        // Only set imageryProvider if we're using fallback (OSM)
        if (imageryProvider) {
            viewerOptions.imageryProvider = imageryProvider;
        }
        
        state.cesiumViewer = new Cesium.Viewer('cesiumContainer', viewerOptions);
        
        // Show fallback notice if using free resources
        if (usingFallback) {
            showCesiumFallbackNotice();
        }
        
    } catch (error) {
        console.error('Failed to initialize Cesium viewer:', error);
        usingFallback = true;
        
        // Create basic viewer with free resources as last resort
        state.cesiumViewer = new Cesium.Viewer('cesiumContainer', {
            terrainProvider: new Cesium.EllipsoidTerrainProvider(),
            imageryProvider: new Cesium.OpenStreetMapImageryProvider({
                url: 'https://a.tile.openstreetmap.org/'
            }),
            baseLayerPicker: false,
            geocoder: false,
            homeButton: true,
            sceneModePicker: true,
            navigationHelpButton: false,
            animation: false,
            timeline: false,
            fullscreenButton: false
        });
        
        showCesiumFallbackNotice();
    }
}

// Show fallback notice in Cesium modal
function showCesiumFallbackNotice() {
    const modal = document.getElementById('cesiumModal');
    let notice = modal.querySelector('.cesium-fallback-notice');
    
    if (!notice) {
        notice = document.createElement('div');
        notice.className = 'cesium-fallback-notice';
        notice.style.cssText = 'position: absolute; top: 70px; left: 10px; background: rgba(0,0,0,0.7); color: white; padding: 8px 12px; border-radius: 4px; font-size: 12px; z-index: 1000; max-width: 300px;';
        notice.innerHTML = '📍 Using OpenStreetMap imagery (no Cesium Ion token)';
        modal.querySelector('.modal-content').appendChild(notice);
    }
}

// Display trajectory in Cesium
function displayTrajectoryInCesium(trajectory) {
    if (!state.cesiumViewer) return;
    
    // Clear existing entities
    state.cesiumViewer.entities.removeAll();
    
    // Create positions array
    const positions = trajectory.map(point => 
        Cesium.Cartesian3.fromDegrees(
            point.longitude_deg,
            point.latitude_deg,
            point.altitude_m
        )
    );
    
    // Add trajectory polyline
    state.cesiumViewer.entities.add({
        name: 'Trajectory',
        polyline: {
            positions: positions,
            width: 5,
            material: new Cesium.PolylineGlowMaterialProperty({
                glowPower: 0.2,
                color: Cesium.Color.CYAN
            }),
            clampToGround: false
        }
    });
    
    // Add launch marker
    state.cesiumViewer.entities.add({
        position: Cesium.Cartesian3.fromDegrees(
            trajectory[0].longitude_deg,
            trajectory[0].latitude_deg,
            0
        ),
        point: {
            pixelSize: 15,
            color: Cesium.Color.BLUE,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2
        },
        label: {
            text: 'Launch',
            font: '14px sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -15)
        }
    });
    
    // Add landing marker
    const lastPoint = trajectory[trajectory.length - 1];
    state.cesiumViewer.entities.add({
        position: Cesium.Cartesian3.fromDegrees(
            lastPoint.longitude_deg,
            lastPoint.latitude_deg,
            0
        ),
        point: {
            pixelSize: 15,
            color: Cesium.Color.RED,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2
        },
        label: {
            text: 'Landing',
            font: '14px sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -15)
        }
    });
    
    // Fly to trajectory
    state.cesiumViewer.flyTo(state.cesiumViewer.entities);
}

// Load config for editor
async function loadConfigForEditor() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const data = await response.json();
            state.currentConfig = data.config;
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// Open settings modal
function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    const editor = document.getElementById('configEditor');
    
    if (state.currentConfig) {
        editor.innerHTML = `
            <textarea id="configTextarea">${JSON.stringify(state.currentConfig, null, 2)}</textarea>
            <div id="configError" class="config-error" style="display: none;"></div>
        `;
    } else {
        editor.innerHTML = '<div class="loading">Loading configuration...</div>';
        loadConfigForEditor().then(() => {
            if (state.currentConfig) {
                editor.innerHTML = `
                    <textarea id="configTextarea">${JSON.stringify(state.currentConfig, null, 2)}</textarea>
                    <div id="configError" class="config-error" style="display: none;"></div>
                `;
            }
        });
    }
    
    modal.classList.add('show');
}

// Open about modal
function openAboutModal() {
    document.getElementById('aboutModal').classList.add('show');
}

// Save config
async function saveConfig() {
    const textarea = document.getElementById('configTextarea');
    const errorDiv = document.getElementById('configError');
    
    if (!textarea) return;
    
    let configData;
    try {
        configData = JSON.parse(textarea.value);
    } catch (error) {
        errorDiv.textContent = 'Invalid JSON: ' + error.message;
        errorDiv.style.display = 'block';
        return;
    }
    
    errorDiv.style.display = 'none';
    showLoading('Saving configuration and rebuilding sweep...');
    
    try {
        const response = await fetch('/api/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configData)
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to save configuration');
        }
        
        state.currentConfig = configData;
        document.getElementById('settingsModal').classList.remove('show');
        
        alert('Configuration saved successfully! Sweep has been rebuilt.');
        
        // Clear current results as they may no longer be valid
        if (state.launch && state.landing) {
            state.lastFeasibilityResult = null;
            state.lastTrajectory = null;
            updateInfoDisplay();
            showEmptyState();
        }
    } catch (error) {
        errorDiv.textContent = error.message;
        errorDiv.style.display = 'block';
    } finally {
        hideLoading();
    }
}

// Show empty state
function showEmptyState() {
    document.getElementById('emptyState').style.display = 'flex';
    document.getElementById('resultsContent').style.display = 'none';
    document.getElementById('show3DBtn').style.display = 'none';
}

// Loading overlay
function showLoading(message) {
    const overlay = document.getElementById('loadingOverlay');
    const messageEl = document.getElementById('loadingMessage');
    messageEl.textContent = message;
    overlay.style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}
