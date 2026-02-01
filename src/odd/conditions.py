"""
Condition Monitor
Safety-Critical Adaptive AI Race Coaching System

Monitors environmental and vehicle conditions for ODD compliance.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum, auto


class WeatherCondition(Enum):
    """Weather conditions."""
    DRY = auto()
    DAMP = auto()
    WET = auto()
    STANDING_WATER = auto()
    UNKNOWN = auto()


class VisibilityLevel(Enum):
    """Visibility levels."""
    CLEAR = auto()
    HAZE = auto()
    FOG = auto()
    RAIN = auto()
    UNKNOWN = auto()


@dataclass
class OperatingConditions:
    """Current operating conditions snapshot."""
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Weather
    weather: WeatherCondition = WeatherCondition.DRY
    visibility: VisibilityLevel = VisibilityLevel.CLEAR
    
    # Temperature
    ambient_temp_c: Optional[float] = None
    track_temp_c: Optional[float] = None
    
    # Surface
    surface_type: str = "asphalt"
    surface_condition: str = "normal"
    
    # Grip estimate
    estimated_grip_multiplier: float = 1.0
    
    # Confidence in conditions
    conditions_confidence: float = 1.0


class ConditionMonitor:
    """
    Monitors and estimates current operating conditions.
    
    Uses available sensors and user input to estimate:
    - Weather conditions
    - Track surface state
    - Grip levels
    
    SAFETY: When conditions are uncertain, assume worst case.
    """
    
    def __init__(self):
        self._current_conditions = OperatingConditions()
        self._condition_history: List[OperatingConditions] = []
        self._max_history = 100
        
        # User overrides
        self._weather_override: Optional[WeatherCondition] = None
        self._surface_override: Optional[str] = None
    
    def update_from_sensors(
        self,
        ambient_temp_c: Optional[float] = None,
        track_temp_c: Optional[float] = None,
        estimated_grip: Optional[float] = None
    ) -> OperatingConditions:
        """
        Update conditions from sensor data.
        
        Args:
            ambient_temp_c: Ambient temperature (if available)
            track_temp_c: Track temperature (if available)
            estimated_grip: Estimated grip multiplier
            
        Returns:
            Updated conditions
        """
        conditions = OperatingConditions(
            timestamp=datetime.now(),
            weather=self._weather_override or self._estimate_weather(),
            visibility=self._estimate_visibility(),
            ambient_temp_c=ambient_temp_c,
            track_temp_c=track_temp_c,
            surface_type=self._surface_override or self._current_conditions.surface_type,
            surface_condition=self._current_conditions.surface_condition,
            estimated_grip_multiplier=estimated_grip or 1.0,
            conditions_confidence=self._compute_confidence()
        )
        
        self._current_conditions = conditions
        self._record_history(conditions)
        
        return conditions
    
    def set_weather(self, weather: WeatherCondition) -> None:
        """Manually set weather condition."""
        self._weather_override = weather
        
        # Adjust grip estimate based on weather
        if weather == WeatherCondition.DRY:
            self._current_conditions.estimated_grip_multiplier = 1.0
        elif weather == WeatherCondition.DAMP:
            self._current_conditions.estimated_grip_multiplier = 0.7
        elif weather == WeatherCondition.WET:
            self._current_conditions.estimated_grip_multiplier = 0.5
        elif weather == WeatherCondition.STANDING_WATER:
            self._current_conditions.estimated_grip_multiplier = 0.3
    
    def set_surface(self, surface_type: str, condition: str = "normal") -> None:
        """Manually set surface type and condition."""
        self._surface_override = surface_type
        self._current_conditions.surface_type = surface_type
        self._current_conditions.surface_condition = condition
    
    def _estimate_weather(self) -> WeatherCondition:
        """Estimate weather from available data."""
        # In a real system, this could use:
        # - Wiper activity
        # - Light sensor
        # - External weather API
        # - Grip estimates from telemetry
        
        # Default to unknown if no override
        return WeatherCondition.DRY
    
    def _estimate_visibility(self) -> VisibilityLevel:
        """Estimate visibility."""
        # In a real system, could use camera analysis
        return VisibilityLevel.CLEAR
    
    def _compute_confidence(self) -> float:
        """Compute confidence in current conditions."""
        confidence = 1.0
        
        # Reduce confidence if using defaults
        if self._weather_override is None:
            confidence *= 0.8
        
        # Reduce confidence if temperatures unknown
        if self._current_conditions.ambient_temp_c is None:
            confidence *= 0.9
        
        if self._current_conditions.track_temp_c is None:
            confidence *= 0.9
        
        return confidence
    
    def _record_history(self, conditions: OperatingConditions) -> None:
        """Record conditions to history."""
        self._condition_history.append(conditions)
        if len(self._condition_history) > self._max_history:
            self._condition_history.pop(0)
    
    def detect_condition_change(self) -> Optional[str]:
        """Detect if conditions have changed significantly."""
        if len(self._condition_history) < 2:
            return None
        
        previous = self._condition_history[-2]
        current = self._condition_history[-1]
        
        changes = []
        
        if previous.weather != current.weather:
            changes.append(f"Weather: {previous.weather.name} -> {current.weather.name}")
        
        if previous.ambient_temp_c and current.ambient_temp_c:
            delta = abs(current.ambient_temp_c - previous.ambient_temp_c)
            if delta > 5.0:
                changes.append(f"Temp change: {delta:.0f}°C")
        
        if abs(previous.estimated_grip_multiplier - current.estimated_grip_multiplier) > 0.1:
            changes.append(f"Grip: {previous.estimated_grip_multiplier:.1f} -> {current.estimated_grip_multiplier:.1f}")
        
        if changes:
            return "; ".join(changes)
        
        return None
    
    @property
    def current_conditions(self) -> OperatingConditions:
        """Get current conditions."""
        return self._current_conditions
    
    @property
    def is_dry(self) -> bool:
        """Check if conditions are dry."""
        return self._current_conditions.weather == WeatherCondition.DRY
    
    @property
    def grip_multiplier(self) -> float:
        """Get current grip multiplier estimate."""
        return self._current_conditions.estimated_grip_multiplier
    
    def reset(self) -> None:
        """Reset monitor state."""
        self._current_conditions = OperatingConditions()
        self._condition_history.clear()
        self._weather_override = None
        self._surface_override = None
