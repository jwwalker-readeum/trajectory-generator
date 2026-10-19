"""Test to specifically check G-Load chart rendering in isolation."""

import pytest
import time
import subprocess
import signal
import os


@pytest.fixture(scope="module")
def server():
    """Start the uvicorn server in the background."""
    env = os.environ.copy()
    env['PYTHONPATH'] = '/workspace/src'
    
    process = subprocess.Popen(
        ['python3', '-m', 'uvicorn', 'trajgen.main:app', '--host', '0.0.0.0', '--port', '8767'],
        cwd='/workspace',
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # Wait for server to start
    time.sleep(5)
    
    yield 'http://localhost:8767'
    
    # Cleanup
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    process.wait(timeout=5)


def test_gload_chart_renders_visually(page, server):
    """Test that G-Load chart actually renders pixels, not just creates the object."""
    console_messages = []
    errors = []
    
    page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
    page.on("pageerror", lambda exc: errors.append(f"PageError: {exc}"))
    
    # Navigate and compute trajectory
    page.goto(server)
    page.wait_for_selector('#map', timeout=10000)
    
    page.evaluate("setLaunch(13.556, 144.866);")
    page.evaluate("setLanding(17.229, 133.242);")
    page.click('#computeTrajectoryBtn')
    page.wait_for_selector('#resultsContent', state='visible', timeout=60000)
    time.sleep(3)
    
    # Take screenshot
    page.screenshot(path="/workspace/gload_chart_test.png", full_page=True)
    
    # Get canvas pixel data to verify it's not blank
    canvas_has_pixels = page.evaluate("""
        (function() {
            const canvas = document.getElementById('gLoadTimeChart');
            if (!canvas) return { error: 'Canvas not found' };
            
            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            // Check if canvas has any non-white pixels
            let hasColor = false;
            for (let i = 0; i < data.length; i += 4) {
                const r = data[i];
                const g = data[i + 1];
                const b = data[i + 2];
                const a = data[i + 3];
                
                // If we find any pixel that's not white (255,255,255) or transparent
                if (a > 0 && (r !== 255 || g !== 255 || b !== 255)) {
                    hasColor = true;
                    break;
                }
            }
            
            return {
                width: canvas.width,
                height: canvas.height,
                hasColor: hasColor,
                totalPixels: data.length / 4
            };
        })()
    """)
    
    print(f"\nCanvas pixel analysis: {canvas_has_pixels}")
    
    # Check chart rendering status
    chart_status = page.evaluate("""
        (function() {
            const chart = state.gLoadTimeChart;
            if (!chart) return { error: 'Chart not found in state' };
            
            return {
                isDestroyed: chart._destroyed || false,
                datasetCount: chart.data?.datasets?.length,
                dataset0Points: chart.data?.datasets[0]?.data?.length,
                dataset1Points: chart.data?.datasets[1]?.data?.length,
                chartType: chart.config?.type,
                hasOptions: chart.options !== undefined,
                hasAnnotation: chart.options?.plugins?.annotation !== undefined,
                annotationEnabled: chart.options?.plugins?.annotation?.annotations !== undefined
            };
        })()
    """)
    
    print(f"\nChart status: {chart_status}")
    
    # Print console messages
    if console_messages:
        print("\n=== Console Messages ===")
        for msg in console_messages[-20:]:  # Last 20 messages
            print(msg)
    
    if errors:
        print("\n=== Errors ===")
        for error in errors:
            print(error)
    
    # Assertions
    assert 'error' not in canvas_has_pixels, f"Canvas error: {canvas_has_pixels}"
    assert canvas_has_pixels['width'] > 0, "Canvas has zero width"
    assert canvas_has_pixels['height'] > 0, "Canvas has zero height"
    assert canvas_has_pixels['hasColor'], "Canvas is blank (no colored pixels found)"
    
    assert 'error' not in chart_status, f"Chart error: {chart_status}"
    assert not chart_status['isDestroyed'], "Chart is destroyed"
    assert chart_status['dataset0Points'] > 0, "Chart dataset 0 has no data points"
