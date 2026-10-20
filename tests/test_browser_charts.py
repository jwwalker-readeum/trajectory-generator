"""Browser-based test for chart rendering using Playwright.

This test actually loads the page in a headless browser and verifies
that all four charts render correctly with data after computing a trajectory.
"""

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
        ['python3', '-m', 'uvicorn', 'trajgen.main:app', '--host', '0.0.0.0', '--port', '8765'],
        cwd='/workspace',
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # Wait for server to start
    time.sleep(5)
    
    yield 'http://localhost:8765'
    
    # Cleanup
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    process.wait(timeout=5)


def test_all_charts_render_with_data(page, server):
    """Test that all four charts render with data after computing a trajectory.
    
    This test reproduces John's exact test case:
    - Launch: 13.556, 144.866
    - Landing: 17.229, 133.242
    - Range: ~1311 km (feasible)
    """
    console_messages = []
    errors = []
    
    # Collect console messages and errors
    page.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    
    # Navigate to the application
    page.goto(server)
    
    # Wait for map to load
    page.wait_for_selector('#map', timeout=10000)
    
    # Set launch point by executing JavaScript directly
    page.evaluate("""
        setLaunch(13.556, 144.866);
    """)
    
    # Set landing point
    page.evaluate("""
        setLanding(17.229, 133.242);
    """)
    
    # Click compute trajectory button
    page.click('#computeTrajectoryBtn')
    
    # Wait for results to appear (trajectory computation can take time)
    page.wait_for_selector('#resultsContent', state='visible', timeout=60000)
    
    # Wait a bit for charts to render
    time.sleep(2)
    
    # Check that all four chart canvases exist
    altitude_range_canvas = page.query_selector('#altitudeRangeChart')
    altitude_time_canvas = page.query_selector('#altitudeTimeChart')
    mach_time_canvas = page.query_selector('#machTimeChart')
    gload_time_canvas = page.query_selector('#gLoadTimeChart')
    
    assert altitude_range_canvas is not None, "Altitude vs Range canvas not found"
    assert altitude_time_canvas is not None, "Altitude vs Time canvas not found"
    assert mach_time_canvas is not None, "Mach vs Time canvas not found"
    assert gload_time_canvas is not None, "G-Load vs Time canvas not found"
    
    # Check canvas dimensions (should not be 0x0)
    altitude_range_box = altitude_range_canvas.bounding_box()
    altitude_time_box = altitude_time_canvas.bounding_box()
    mach_time_box = mach_time_canvas.bounding_box()
    gload_time_box = gload_time_canvas.bounding_box()
    
    assert altitude_range_box['width'] > 0 and altitude_range_box['height'] > 0, \
        "Altitude vs Range canvas has zero dimensions"
    assert altitude_time_box['width'] > 0 and altitude_time_box['height'] > 0, \
        "Altitude vs Time canvas has zero dimensions"
    assert mach_time_box['width'] > 0 and mach_time_box['height'] > 0, \
        "Mach vs Time canvas has zero dimensions"
    assert gload_time_box['width'] > 0 and gload_time_box['height'] > 0, \
        "G-Load vs Time canvas has zero dimensions"
    
    # Check that Chart.js charts actually exist in state
    charts_exist = page.evaluate("""
        ({
            altitudeRange: state.altitudeRangeChart !== null,
            altitudeTime: state.altitudeTimeChart !== null,
            machTime: state.machTimeChart !== null,
            gLoadTime: state.gLoadTimeChart !== null
        })
    """)
    
    assert charts_exist['altitudeRange'], "Altitude vs Range chart not created in state"
    assert charts_exist['altitudeTime'], "Altitude vs Time chart not created in state"
    assert charts_exist['machTime'], "Mach vs Time chart not created in state"
    assert charts_exist['gLoadTime'], "G-Load vs Time chart not created in state"
    
    # Check that charts have data
    chart_data_counts = page.evaluate("""
        ({
            altitudeRange: state.altitudeRangeChart?.data?.datasets[0]?.data?.length || 0,
            altitudeTime: state.altitudeTimeChart?.data?.datasets[0]?.data?.length || 0,
            machTime: state.machTimeChart?.data?.datasets[0]?.data?.length || 0,
            gLoadTime: state.gLoadTimeChart?.data?.datasets[0]?.data?.length || 0
        })
    """)
    
    assert chart_data_counts['altitudeRange'] > 0, \
        f"Altitude vs Range chart has no data (count: {chart_data_counts['altitudeRange']})"
    assert chart_data_counts['altitudeTime'] > 0, \
        f"Altitude vs Time chart has no data (count: {chart_data_counts['altitudeTime']})"
    assert chart_data_counts['machTime'] > 0, \
        f"Mach vs Time chart has no data (count: {chart_data_counts['machTime']})"
    assert chart_data_counts['gLoadTime'] > 0, \
        f"G-Load vs Time chart has no data (count: {chart_data_counts['gLoadTime']})"
    
    # Take a screenshot for debugging
    page.screenshot(path="/workspace/test_charts_screenshot.png", full_page=True)
    
    # Print console messages and errors for debugging
    print("\n=== Console Messages ===")
    for msg in console_messages:
        print(msg)
    
    if errors:
        print("\n=== JavaScript Errors ===")
        for error in errors:
            print(error)
        pytest.fail(f"JavaScript errors occurred: {errors}")
    
    print("\n=== Chart Data Counts ===")
    print(f"Altitude vs Range: {chart_data_counts['altitudeRange']} points")
    print(f"Altitude vs Time: {chart_data_counts['altitudeTime']} points")
    print(f"Mach vs Time: {chart_data_counts['machTime']} points")
    print(f"G-Load vs Time: {chart_data_counts['gLoadTime']} points")


def test_gload_chart_has_peak_marker_and_limit_line(page, server):
    """Test that G-Load chart includes peak marker annotation and limit line."""
    # Navigate and compute trajectory
    page.goto(server)
    page.wait_for_selector('#map', timeout=10000)
    
    page.evaluate("setLaunch(13.556, 144.866);")
    page.evaluate("setLanding(17.229, 133.242);")
    page.click('#computeTrajectoryBtn')
    page.wait_for_selector('#resultsContent', state='visible', timeout=60000)
    time.sleep(2)
    
    # Check that G-Load chart has two datasets (g-load + limit line)
    gload_datasets = page.evaluate("""
        state.gLoadTimeChart?.data?.datasets?.length || 0
    """)
    
    assert gload_datasets == 2, \
        f"G-Load chart should have 2 datasets (g-load + limit line), found {gload_datasets}"
    
    # Check that annotation plugin is configured
    has_annotation = page.evaluate("""
        state.gLoadTimeChart?.options?.plugins?.annotation !== undefined
    """)
    
    assert has_annotation, "G-Load chart should have annotation plugin configured"
    
    # Check that peak annotation exists
    has_peak_annotation = page.evaluate("""
        state.gLoadTimeChart?.options?.plugins?.annotation?.annotations?.peakPoint !== undefined
    """)
    
    assert has_peak_annotation, "G-Load chart should have peak point annotation"
