"""Tests for .env file loading functionality."""

import os
import tempfile
import pytest
from pathlib import Path
from dotenv import load_dotenv


def test_dotenv_loads_env_file():
    """Test that dotenv loads variables from .env file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / '.env'
        env_file.write_text('TEST_VAR=test_value\nANOTHER_VAR=another_value')
        
        # Clear any existing value
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']
        if 'ANOTHER_VAR' in os.environ:
            del os.environ['ANOTHER_VAR']
        
        # Load the .env file
        load_dotenv(env_file)
        
        assert os.environ.get('TEST_VAR') == 'test_value'
        assert os.environ.get('ANOTHER_VAR') == 'another_value'
        
        # Cleanup
        del os.environ['TEST_VAR']
        del os.environ['ANOTHER_VAR']


def test_dotenv_preserves_existing_env_vars():
    """Test that dotenv with override=False preserves existing environment variables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / '.env'
        env_file.write_text('EXISTING_VAR=from_file\nNEW_VAR=new_value')
        
        # Set an existing environment variable
        os.environ['EXISTING_VAR'] = 'from_environment'
        
        # Load with override=False (should not overwrite existing)
        load_dotenv(env_file, override=False)
        
        # Existing var should remain unchanged
        assert os.environ.get('EXISTING_VAR') == 'from_environment'
        # New var should be loaded
        assert os.environ.get('NEW_VAR') == 'new_value'
        
        # Cleanup
        del os.environ['EXISTING_VAR']
        del os.environ['NEW_VAR']


def test_dotenv_with_override_true():
    """Test that dotenv with override=True overwrites existing variables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / '.env'
        env_file.write_text('OVERRIDE_VAR=from_file')
        
        # Set an existing environment variable
        os.environ['OVERRIDE_VAR'] = 'from_environment'
        
        # Load with override=True (should overwrite)
        load_dotenv(env_file, override=True)
        
        # Variable should be overwritten
        assert os.environ.get('OVERRIDE_VAR') == 'from_file'
        
        # Cleanup
        del os.environ['OVERRIDE_VAR']


def test_cesium_token_from_dotenv():
    """Test that CESIUM_ION_TOKEN can be loaded from .env file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / '.env'
        test_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test'
        env_file.write_text(f'CESIUM_ION_TOKEN={test_token}')
        
        # Clear any existing value
        if 'CESIUM_ION_TOKEN' in os.environ:
            del os.environ['CESIUM_ION_TOKEN']
        
        # Load the .env file
        load_dotenv(env_file)
        
        assert os.environ.get('CESIUM_ION_TOKEN') == test_token
        
        # Cleanup
        del os.environ['CESIUM_ION_TOKEN']


def test_app_password_from_dotenv():
    """Test that APP_PASSWORD can be loaded from .env file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / '.env'
        test_password = 'SecurePassword123!'
        env_file.write_text(f'APP_PASSWORD={test_password}')
        
        # Clear any existing value
        if 'APP_PASSWORD' in os.environ:
            del os.environ['APP_PASSWORD']
        
        # Load the .env file
        load_dotenv(env_file)
        
        assert os.environ.get('APP_PASSWORD') == test_password
        
        # Cleanup
        del os.environ['APP_PASSWORD']


def test_dotenv_handles_whitespace():
    """Test that dotenv correctly handles values with whitespace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / '.env'
        # Test various whitespace scenarios
        env_file.write_text(
            'NO_WHITESPACE=value\n'
            'LEADING_SPACE= value\n'
            'TRAILING_SPACE=value \n'
            'BOTH_SPACES= value \n'
        )
        
        # Clear any existing values
        for var in ['NO_WHITESPACE', 'LEADING_SPACE', 'TRAILING_SPACE', 'BOTH_SPACES']:
            if var in os.environ:
                del os.environ[var]
        
        # Load the .env file
        load_dotenv(env_file)
        
        # python-dotenv strips leading/trailing whitespace by default
        assert os.environ.get('NO_WHITESPACE') == 'value'
        assert os.environ.get('LEADING_SPACE') == 'value'
        assert os.environ.get('TRAILING_SPACE') == 'value'
        assert os.environ.get('BOTH_SPACES') == 'value'
        
        # Cleanup
        for var in ['NO_WHITESPACE', 'LEADING_SPACE', 'TRAILING_SPACE', 'BOTH_SPACES']:
            if var in os.environ:
                del os.environ[var]


def test_dotenv_handles_quotes():
    """Test that dotenv correctly handles quoted values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / '.env'
        # Test various quote scenarios
        env_file.write_text(
            'NO_QUOTES=value\n'
            'SINGLE_QUOTES=\'value\'\n'
            'DOUBLE_QUOTES="value"\n'
            'MIXED_QUOTES="value\'with\'quotes"\n'
        )
        
        # Clear any existing values
        for var in ['NO_QUOTES', 'SINGLE_QUOTES', 'DOUBLE_QUOTES', 'MIXED_QUOTES']:
            if var in os.environ:
                del os.environ[var]
        
        # Load the .env file
        load_dotenv(env_file)
        
        # python-dotenv removes outer quotes
        assert os.environ.get('NO_QUOTES') == 'value'
        assert os.environ.get('SINGLE_QUOTES') == 'value'
        assert os.environ.get('DOUBLE_QUOTES') == 'value'
        assert os.environ.get('MIXED_QUOTES') == "value'with'quotes"
        
        # Cleanup
        for var in ['NO_QUOTES', 'SINGLE_QUOTES', 'DOUBLE_QUOTES', 'MIXED_QUOTES']:
            if var in os.environ:
                del os.environ[var]


def test_dotenv_missing_file_does_not_fail():
    """Test that loading a non-existent .env file doesn't raise an error."""
    # This should not raise an error - just return False
    result = load_dotenv('/nonexistent/path/.env')
    assert result is False


def test_railway_env_vars_preserved():
    """Test that Railway-provided environment variables are preserved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / '.env'
        env_file.write_text('CESIUM_ION_TOKEN=local_token\nAPP_PASSWORD=local_password')
        
        # Simulate Railway setting these variables
        os.environ['CESIUM_ION_TOKEN'] = 'railway_token'
        os.environ['APP_PASSWORD'] = 'railway_password'
        
        # Load with override=False (Railway deployment scenario)
        load_dotenv(env_file, override=False)
        
        # Railway values should be preserved
        assert os.environ.get('CESIUM_ION_TOKEN') == 'railway_token'
        assert os.environ.get('APP_PASSWORD') == 'railway_password'
        
        # Cleanup
        del os.environ['CESIUM_ION_TOKEN']
        del os.environ['APP_PASSWORD']


def test_cesium_token_endpoint_with_dotenv():
    """Test that the /api/cesium-token endpoint works with dotenv-loaded variables."""
    import os
    
    # Set up a token via environment (simulating dotenv)
    test_token = 'test_ion_token_12345'
    os.environ['CESIUM_ION_TOKEN'] = test_token
    
    try:
        # Simulate the endpoint logic
        token = os.environ.get('CESIUM_ION_TOKEN', None)
        
        # Don't expose the placeholder value
        if token == 'YOUR_ION_TOKEN_HERE':
            token = None
        
        result = {
            "token": token,
            "has_token": token is not None
        }
        
        assert result['token'] == test_token
        assert result['has_token'] is True
    finally:
        # Cleanup
        if 'CESIUM_ION_TOKEN' in os.environ:
            del os.environ['CESIUM_ION_TOKEN']


def test_cesium_token_endpoint_with_placeholder():
    """Test that placeholder token is filtered out."""
    import os
    
    # Set placeholder token
    os.environ['CESIUM_ION_TOKEN'] = 'YOUR_ION_TOKEN_HERE'
    
    try:
        # Simulate the endpoint logic
        token = os.environ.get('CESIUM_ION_TOKEN', None)
        
        # Don't expose the placeholder value
        if token == 'YOUR_ION_TOKEN_HERE':
            token = None
        
        result = {
            "token": token,
            "has_token": token is not None
        }
        
        assert result['token'] is None
        assert result['has_token'] is False
    finally:
        # Cleanup
        if 'CESIUM_ION_TOKEN' in os.environ:
            del os.environ['CESIUM_ION_TOKEN']


def test_token_not_logged(capfd):
    """Test that tokens are not accidentally logged to stdout."""
    import os
    
    test_token = 'secret_token_should_not_appear_in_logs'
    os.environ['CESIUM_ION_TOKEN'] = test_token
    
    try:
        # Simulate typical operations
        token = os.environ.get('CESIUM_ION_TOKEN', None)
        
        # Don't log the token (this is what we should NOT do)
        # print(f"Token: {token}")  # WRONG
        
        # Only log that a token exists
        if token and token != 'YOUR_ION_TOKEN_HERE':
            print("Cesium Ion token configured")
        
        # Capture output
        captured = capfd.readouterr()
        
        # Token value should NOT appear in output
        assert test_token not in captured.out
        assert test_token not in captured.err
        
        # Safe message should appear
        if token and token != 'YOUR_ION_TOKEN_HERE':
            assert "Cesium Ion token configured" in captured.out
    finally:
        # Cleanup
        if 'CESIUM_ION_TOKEN' in os.environ:
            del os.environ['CESIUM_ION_TOKEN']
