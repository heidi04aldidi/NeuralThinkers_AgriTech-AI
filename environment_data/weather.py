"""
Weather API Integration Module

This module handles OpenWeatherMap API integration for weather data.
"""

from typing import Optional, Dict, Any
import requests

from .config import get_openweather_api_key, get_api_timeout


def fetch_weather_data(
    latitude: float, 
    longitude: float,
    timeout: Optional[int] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch current weather data from OpenWeatherMap API.
    
    Args:
        latitude: GPS latitude coordinate
        longitude: GPS longitude coordinate
        
    Returns:
        Optional[Dict]: Raw weather API response or None if failed
    """
    try:
        api_key = get_openweather_api_key()
        
        # OpenWeatherMap Current Weather endpoint
        url = "https://api.openweathermap.org/data/2.5/weather"
        
        # Parameters for the API call
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": api_key,
            "units": "metric"  # Get temperature in Celsius
        }
        
        # Use provided timeout or get from config
        request_timeout = timeout if timeout is not None else get_api_timeout()
        
        # Make the API request with timeout
        response = requests.get(url, params=params, timeout=request_timeout)
        
        # Check if request was successful (status code 200)
        if response.status_code == 401:
            print("Error: Invalid OpenWeatherMap API key")
            return None
        
        if response.status_code == 404:
            print("Error: Location not found by OpenWeatherMap")
            return None
        
        response.raise_for_status()  # Raise error for other bad status codes
        
        # Parse JSON response
        return response.json()
        
    except requests.exceptions.Timeout:
        print("Error: Weather API request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error in fetch_weather_data: {str(e)}")
        return None


def process_weather_data(raw_weather: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize raw OpenWeatherMap response into standardized format.
    
    Args:
        raw_weather: Raw JSON response from OpenWeatherMap API
        
    Returns:
        Dict: Normalized weather data with keys:
            - temperature_c: Temperature in Celsius
            - humidity: Humidity percentage
            - rainfall_mm: Rainfall in mm (or None if not available)
            - weather_alert: Simple weather alert string (or None)
    """
    try:
        # Extract main weather data
        main_data = raw_weather.get("main", {})
        
        # Get temperature in Celsius
        temperature_c = main_data.get("temp")
        
        # Get humidity as percentage
        humidity = main_data.get("humidity")
        
        # Try to get rainfall data from "rain" key (in mm, last 1 hour)
        rain_data = raw_weather.get("rain", {})
        rainfall_mm = rain_data.get("1h")  # Rainfall in last 1 hour
        
        # If no 1-hour data, check for 3-hour data
        if rainfall_mm is None:
            rainfall_mm = rain_data.get("3h")
        
        # Generate simple weather alert using rule-based logic
        weather_alert = generate_weather_alert(temperature_c, humidity, rainfall_mm)
        
        return {
            "temperature_c": float(temperature_c) if temperature_c is not None else None,
            "humidity": int(humidity) if humidity is not None else None,
            "rainfall_mm": float(rainfall_mm) if rainfall_mm is not None else None,
            "weather_alert": weather_alert
        }
        
    except Exception as e:
        print(f"Error processing weather data: {str(e)}")
        return {
            "temperature_c": None,
            "humidity": None,
            "rainfall_mm": None,
            "weather_alert": None
        }


def generate_weather_alert(
    temperature_c: Optional[float], 
    humidity: Optional[int], 
    rainfall_mm: Optional[float]
) -> Optional[str]:
    """
    Generate simple weather alerts based on rule-based logic.
    
    This creates alerts for conditions that might affect farming:
    - High rainfall (flood risk)
    - Extreme temperatures
    - High humidity (disease risk)
    
    Args:
        temperature_c: Temperature in Celsius
        humidity: Humidity percentage
        rainfall_mm: Rainfall in mm
        
    Returns:
        Optional[str]: Alert message or None if no alert conditions met
    """
    alerts = []
    
    # Check for heavy rainfall (potential flood risk)
    if rainfall_mm is not None:
        if rainfall_mm > 10:
            alerts.append("HIGH FLOOD RISK: Heavy rainfall detected")
        elif rainfall_mm > 5:
            alerts.append("MODERATE RAINFALL: Possible water accumulation")
    
    # Check for extreme temperatures
    if temperature_c is not None:
        if temperature_c > 40:
            alerts.append("HEAT ALERT: Extreme high temperature")
        elif temperature_c < 0:
            alerts.append("FROST ALERT: Freezing temperature detected")
        elif temperature_c > 35:
            alerts.append("HEAT STRESS: High temperature warning")
        elif temperature_c < 5:
            alerts.append("COLD STRESS: Low temperature warning")
    
    # Check for high humidity (disease risk)
    if humidity is not None:
        if humidity > 90:
            alerts.append("DISEASE RISK: Very high humidity")
        elif humidity > 80:
            alerts.append("DISEASE WARNING: High humidity conditions")
    
    # Return first alert or None
    return alerts[0] if alerts else None

