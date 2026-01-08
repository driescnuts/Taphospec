"""Version information for TaphoSpec"""

__version__ = "2.0.0"
__author__ = "Dries Cnuts"
__institution__ = "TraceoLab, University of Liège"
__license__ = "MIT"
__copyright__ = "Copyright 2024-2026 TraceoLab"

def get_version():
    """Return version string"""
    return __version__

def print_version():
    """Print version information"""
    print(f"TaphoSpec v{__version__}")
    print(f"Author: {__author__}")
    print(f"Institution: {__institution__}")
    print(f"License: {__license__}")
