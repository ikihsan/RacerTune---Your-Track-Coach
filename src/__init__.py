# Safety-Critical Adaptive AI Race Coaching System
# Main package initialization

from .system import (
    CoachingSystem,
    SystemConfig,
    get_system,
    initialize_system
)

__version__ = "0.1.0"
__author__ = "Safety-Critical Systems Team"

__all__ = [
    "CoachingSystem",
    "SystemConfig",
    "get_system",
    "initialize_system"
]
