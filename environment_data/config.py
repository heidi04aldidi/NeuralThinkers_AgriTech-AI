"""
Configuration Module - API Key Loading

This module handles loading of API keys from environment variables.
"""

import os


# Default timeout for API requests in seconds
DEFAULT_API_TIMEOUT = 10


def get_api_timeout() -> int:
    """
    Get API timeout from environment variable or use default.
    
    Returns:
        int: Timeout in seconds for API requests
    """
    timeout_str = os.environ.get("API_TIMEOUT")
    if timeout_str:
        try:
            timeout = int(timeout_str)
            if timeout > 0:
                return timeout
        except ValueError:
            pass
    return DEFAULT_API_TIMEOUT


def get_openweather_api_key() -> str:
    """
    Get OpenWeatherMap API key from environment variables.
    
    Returns:
        str: API key for OpenWeatherMap
        
    Raises:
        ValueError: If API key is not set
    """
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENWEATHER_API_KEY environment variable is not set. "
            "Please set it before calling get_environmental_context()"
        )
    return api_key


def get_ambee_api_key() -> str:
    """
    Get Ambee API key from environment variables.
    
    Returns:
        str: API key for Ambee
        
    Raises:
        ValueError: If API key is not set
    """
    api_key = os.environ.get("AMBEE_API_KEY")
    if not api_key:
        raise ValueError(
            "AMBEE_API_KEY environment variable is not set. "
            "Please set it before calling get_environmental_context()"
        )
    return api_key

