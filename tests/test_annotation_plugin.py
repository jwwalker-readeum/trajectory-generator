"""Test to check if annotation plugin is properly loaded and registered."""

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
        ['python3', '-m', 'uvicorn', 'trajgen.main:app', '--host', '0.0.0.0', '--port', '8766'],
        cwd='/workspace',
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    
    # Wait for server to start
    time.sleep(5)
    
    yield 'http://localhost:8766'
    
    # Cleanup
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    process.wait(timeout=5)


def test_annotation_plugin_availability(page, server):
    """Test that the annotation plugin is loaded and available."""
    console_messages = []
    warnings = []
    errors = []
    
    # Collect ALL console messages including warnings
    def handle_console(msg):
        text = msg.text
        msg_type = msg.type
        console_messages.append(f"[{msg_type}] {text}")
        if msg_type == 'warning':
            warnings.append(text)
        elif msg_type == 'error':
            errors.append(text)
    
    page.on("console", handle_console)
    page.on("pageerror", lambda exc: errors.append(f"PageError: {exc}"))
    
    # Navigate to the application
    page.goto(server)
    page.wait_for_selector('#map', timeout=10000)
    
    # Check if Chart.js is loaded
    chart_loaded = page.evaluate("typeof Chart !== 'undefined'")
    print(f"\nChart.js loaded: {chart_loaded}")
    
    # Check if annotation plugin is loaded
    annotation_loaded = page.evaluate("""
        typeof ChartAnnotation !== 'undefined' || 
        (typeof Chart !== 'undefined' && typeof Chart.Annotation !== 'undefined')
    """)
    print(f"Annotation plugin loaded: {annotation_loaded}")
    
    # Check what's available
    available_objects = page.evaluate("""
        ({
            Chart: typeof Chart,
            ChartAnnotation: typeof ChartAnnotation,
            ChartDataLabels: typeof ChartDataLabels,
            window_Chart: typeof window.Chart
        })
    """)
    print(f"Available objects: {available_objects}")
    
    # Check if annotation is registered
    is_registered = page.evaluate("""
        (function() {
            if (typeof Chart === 'undefined') return false;
            if (!Chart.registry) return false;
            return Chart.registry.plugins.get('annotation') !== undefined;
        })()
    """)
    print(f"Annotation plugin registered: {is_registered}")
    
    # Now compute a trajectory and check for warnings
    page.evaluate("setLaunch(13.556, 144.866);")
    page.evaluate("setLanding(17.229, 133.242);")
    page.click('#computeTrajectoryBtn')
    page.wait_for_selector('#resultsContent', state='visible', timeout=60000)
    time.sleep(2)
    
    # Print all console messages
    print("\n=== All Console Messages ===")
    for msg in console_messages:
        print(msg)
    
    if warnings:
        print("\n=== Warnings ===")
        for w in warnings:
            print(w)
    
    if errors:
        print("\n=== Errors ===")
        for e in errors:
            print(e)
    
    # Check if gload chart was created
    gload_exists = page.evaluate("state.gLoadTimeChart !== null")
    print(f"\nG-Load chart created: {gload_exists}")
    
    if gload_exists:
        # Check chart details
        chart_info = page.evaluate("""
            (function() {
                const chart = state.gLoadTimeChart;
                return {
                    hasData: chart.data?.datasets?.length > 0,
                    datasetCount: chart.data?.datasets?.length,
                    firstDatasetPoints: chart.data?.datasets[0]?.data?.length,
                    hasAnnotationConfig: chart.options?.plugins?.annotation !== undefined,
                    annotationKeys: chart.options?.plugins?.annotation ? 
                        Object.keys(chart.options.plugins.annotation) : []
                };
            })()
        """)
        print(f"\nG-Load chart info: {chart_info}")
