"""
Environment Data Package

This package provides a clean Python interface to fetch and normalize
environmental data (weather and soil) from external APIs.

Usage:
    from environment_data.wrapper import get_environmental_context
    
    # Get all environmental data
    data = get_environmental_context()
    print(data)
"""

from environment_data.wrapper import get_environmental_context

__all__ = ["get_environmental_context"]

