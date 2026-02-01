"""
ODD Validator
Safety-Critical Adaptive AI Race Coaching System

Validates that system is operating within its design domain.

SAFETY: System must only operate within defined ODD.
Outside ODD, system must go silent or warn driver.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List, Set
import yaml


class ODDViolationType(Enum):
    """Types of ODD violations."""
    
    NONE = auto()
    
    # Environment
    WEATHER_VIOLATION = auto()
    VISIBILITY_VIOLATION = auto()
    TEMPERATURE_VIOLATION = auto()
    
    # Track
    TRACK_TYPE_VIOLATION = auto()
    SURFACE_VIOLATION = auto()
    
    # Vehicle
    VEHICLE_TYPE_VIOLATION = auto()
    SPEED_VIOLATION = auto()
    
    # Sensor
    SENSOR_UNAVAILABLE = auto()
    SENSOR_DEGRADED = auto()
    
    # System
    CONFIDENCE_VIOLATION = auto()
    DATA_STALE = auto()


@dataclass
class ODDViolation:
    """Represents an ODD violation."""
    
    violation_type: ODDViolationType
    severity: str  # "warning", "degraded", "stop"
    message: str
    recommendation: str
    
    @property
    def is_blocking(self) -> bool:
        """Check if violation blocks operation."""
        return self.severity in ["degraded", "stop"]


@dataclass
class ODDDefinition:
    """Definition of Operational Design Domain."""
    
    # Track types
    allowed_track_types: Set[str]
    
    # Weather
    weather_allowed: Set[str]
    max_wind_speed_kmh: float
    
    # Temperature
    min_ambient_temp_c: float
    max_ambient_temp_c: float
    min_track_temp_c: float
    max_track_temp_c: float
    
    # Speed
    max_speed_kmh: float
    
    # Sensors
    required_sensors: Set[str]
    min_gps_accuracy_m: float
    min_gps_hz: float
    
    # Confidence
    min_operating_confidence: float
    
    @classmethod
    def load_from_yaml(cls, path: str) -> "ODDDefinition":
        """Load ODD definition from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        track = data.get("track_environment", {})
        env = data.get("environmental_constraints", {})
        sensors = data.get("sensor_requirements", {})
        
        return cls(
            allowed_track_types=set(track.get("allowed_types", ["closed_circuit"])),
            weather_allowed=set(env.get("weather_conditions", ["dry"])),
            max_wind_speed_kmh=env.get("max_wind_speed_kmh", 50.0),
            min_ambient_temp_c=env.get("temperature_range_c", {}).get("min", 0),
            max_ambient_temp_c=env.get("temperature_range_c", {}).get("max", 45),
            min_track_temp_c=env.get("track_temperature_c", {}).get("min", 5),
            max_track_temp_c=env.get("track_temperature_c", {}).get("max", 60),
            max_speed_kmh=300.0,  # Default max
            required_sensors=set(sensors.get("gps", {}).keys()) | {"gps"},
            min_gps_accuracy_m=sensors.get("gps", {}).get("minimum_accuracy_m", 3.0),
            min_gps_hz=sensors.get("gps", {}).get("minimum_hz", 10),
            min_operating_confidence=0.7
        )
    
    @classmethod
    def default(cls) -> "ODDDefinition":
        """Get default ODD definition."""
        return cls(
            allowed_track_types={"closed_circuit", "karting"},
            weather_allowed={"dry"},
            max_wind_speed_kmh=50.0,
            min_ambient_temp_c=0.0,
            max_ambient_temp_c=45.0,
            min_track_temp_c=5.0,
            max_track_temp_c=60.0,
            max_speed_kmh=300.0,
            required_sensors={"gps"},
            min_gps_accuracy_m=3.0,
            min_gps_hz=10.0,
            min_operating_confidence=0.7
        )


@dataclass
class CurrentConditions:
    """Current operating conditions."""
    
    # Track
    track_type: str = "closed_circuit"
    surface_type: str = "asphalt"
    
    # Weather
    weather: str = "dry"
    wind_speed_kmh: float = 0.0
    
    # Temperature
    ambient_temp_c: float = 20.0
    track_temp_c: float = 30.0
    
    # Vehicle
    current_speed_kmh: float = 0.0
    
    # Sensors
    gps_available: bool = True
    gps_accuracy_m: float = 1.0
    gps_hz: float = 10.0
    imu_available: bool = True
    
    # System
    confidence: float = 1.0
    data_age_ms: float = 0.0


class ODDValidator:
    """
    Validates that system operates within its design domain.
    
    The Operational Design Domain defines the conditions under
    which the system is designed to operate safely. Outside
    the ODD, the system must reduce capability or go silent.
    
    SAFETY PRINCIPLE:
    - ODD is a hard boundary, not a soft suggestion
    - Outside ODD = reduced trust in system outputs
    - Some violations are blocking (must stop coaching)
    - Other violations are warnings (continue with caution)
    """
    
    def __init__(self, odd_definition: Optional[ODDDefinition] = None):
        self.odd = odd_definition or ODDDefinition.default()
        self._current_violations: List[ODDViolation] = []
    
    def validate(self, conditions: CurrentConditions) -> List[ODDViolation]:
        """
        Validate current conditions against ODD.
        
        Args:
            conditions: Current operating conditions
            
        Returns:
            List of ODD violations (empty if compliant)
        """
        violations = []
        
        # Check track type
        if conditions.track_type not in self.odd.allowed_track_types:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.TRACK_TYPE_VIOLATION,
                severity="stop",
                message=f"Track type '{conditions.track_type}' not supported",
                recommendation="System designed for closed circuit only"
            ))
        
        # Check weather
        if conditions.weather not in self.odd.weather_allowed:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.WEATHER_VIOLATION,
                severity="stop",
                message=f"Weather '{conditions.weather}' not supported",
                recommendation="System designed for dry conditions only"
            ))
        
        # Check wind
        if conditions.wind_speed_kmh > self.odd.max_wind_speed_kmh:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.WEATHER_VIOLATION,
                severity="degraded",
                message=f"Wind {conditions.wind_speed_kmh:.0f} km/h exceeds limit",
                recommendation="Reduce reliance on system in high winds"
            ))
        
        # Check temperatures
        if conditions.ambient_temp_c < self.odd.min_ambient_temp_c:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.TEMPERATURE_VIOLATION,
                severity="warning",
                message=f"Ambient temp {conditions.ambient_temp_c:.0f}°C below minimum",
                recommendation="Tire grip may be unpredictable"
            ))
        
        if conditions.ambient_temp_c > self.odd.max_ambient_temp_c:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.TEMPERATURE_VIOLATION,
                severity="warning",
                message=f"Ambient temp {conditions.ambient_temp_c:.0f}°C above maximum",
                recommendation="Tire grip may be unpredictable"
            ))
        
        if conditions.track_temp_c > self.odd.max_track_temp_c:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.TEMPERATURE_VIOLATION,
                severity="degraded",
                message=f"Track temp {conditions.track_temp_c:.0f}°C very high",
                recommendation="Grip levels may be reduced"
            ))
        
        # Check speed
        if conditions.current_speed_kmh > self.odd.max_speed_kmh:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.SPEED_VIOLATION,
                severity="warning",
                message=f"Speed {conditions.current_speed_kmh:.0f} km/h exceeds validated range",
                recommendation="System accuracy unverified at this speed"
            ))
        
        # Check GPS
        if not conditions.gps_available:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.SENSOR_UNAVAILABLE,
                severity="stop",
                message="GPS unavailable",
                recommendation="Cannot operate without GPS"
            ))
        elif conditions.gps_accuracy_m > self.odd.min_gps_accuracy_m:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.SENSOR_DEGRADED,
                severity="degraded",
                message=f"GPS accuracy {conditions.gps_accuracy_m:.1f}m poor",
                recommendation="Reduce trust in position data"
            ))
        
        if conditions.gps_hz < self.odd.min_gps_hz:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.SENSOR_DEGRADED,
                severity="degraded",
                message=f"GPS rate {conditions.gps_hz:.0f} Hz too low",
                recommendation="May miss rapid changes"
            ))
        
        # Check confidence
        if conditions.confidence < self.odd.min_operating_confidence:
            violations.append(ODDViolation(
                violation_type=ODDViolationType.CONFIDENCE_VIOLATION,
                severity="degraded",
                message=f"System confidence {conditions.confidence:.0%} low",
                recommendation="Reducing coaching output"
            ))
        
        # Check data freshness
        if conditions.data_age_ms > 1000:  # Data older than 1 second
            violations.append(ODDViolation(
                violation_type=ODDViolationType.DATA_STALE,
                severity="degraded",
                message=f"Data {conditions.data_age_ms:.0f}ms old",
                recommendation="Data may not reflect current state"
            ))
        
        self._current_violations = violations
        return violations
    
    def is_within_odd(self, conditions: CurrentConditions) -> bool:
        """Check if conditions are within ODD (no blocking violations)."""
        violations = self.validate(conditions)
        return not any(v.is_blocking for v in violations)
    
    def should_stop_coaching(self, conditions: CurrentConditions) -> bool:
        """Check if coaching should stop entirely."""
        violations = self.validate(conditions)
        return any(v.severity == "stop" for v in violations)
    
    def get_current_violations(self) -> List[ODDViolation]:
        """Get list of current violations."""
        return list(self._current_violations)
    
    def get_blocking_violations(self) -> List[ODDViolation]:
        """Get only blocking violations."""
        return [v for v in self._current_violations if v.is_blocking]
    
    def get_warnings(self) -> List[ODDViolation]:
        """Get warning-level violations."""
        return [v for v in self._current_violations if v.severity == "warning"]
