"""
Telemetry Data Types
Safety-Critical Adaptive AI Race Coaching System

This module defines all sensor data structures with explicit uncertainty modeling.

SAFETY INVARIANT: No sensor data is assumed to be precise or reliable.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Tuple
import math

from .confidence import Confidence


class SensorStatus(Enum):
    """Status of a sensor reading."""
    
    VALID = auto()          # Reading is valid
    STALE = auto()          # Reading is old but usable
    DEGRADED = auto()       # Reading has reduced accuracy
    DROPOUT = auto()        # Temporary loss of signal
    INVALID = auto()        # Reading cannot be used
    SATURATED = auto()      # Sensor at measurement limit
    UNCALIBRATED = auto()   # Sensor not calibrated


@dataclass(frozen=True)
class GPSReading:
    """
    Single GPS position reading with uncertainty.
    
    All position values include explicit uncertainty bounds.
    """
    
    # Timestamp
    timestamp_ms: int
    
    # Position (WGS84)
    latitude_deg: float
    longitude_deg: float
    altitude_m: Optional[float] = None
    
    # Uncertainty
    horizontal_accuracy_m: float = 10.0  # Conservative default
    vertical_accuracy_m: float = 20.0    # Conservative default
    
    # Quality indicators
    hdop: float = 5.0                    # Horizontal dilution of precision
    num_satellites: int = 0
    fix_type: str = "none"               # none, 2D, 3D, DGPS, RTK
    
    # Status
    status: SensorStatus = SensorStatus.VALID
    
    @property
    def confidence(self) -> Confidence:
        """Compute confidence from GPS quality indicators."""
        
        # Start with base confidence from fix type
        base_confidence = {
            "none": 0.0,
            "2D": 0.3,
            "3D": 0.6,
            "DGPS": 0.8,
            "RTK": 0.95
        }.get(self.fix_type, 0.3)
        
        # Degrade based on HDOP
        if self.hdop > 5.0:
            hdop_factor = 0.5
        elif self.hdop > 2.0:
            hdop_factor = 0.7
        elif self.hdop > 1.0:
            hdop_factor = 0.9
        else:
            hdop_factor = 1.0
        
        # Degrade based on satellite count
        if self.num_satellites < 4:
            sat_factor = 0.3
        elif self.num_satellites < 6:
            sat_factor = 0.6
        elif self.num_satellites < 8:
            sat_factor = 0.8
        else:
            sat_factor = 1.0
        
        # Status check
        if self.status != SensorStatus.VALID:
            status_factor = 0.5
        else:
            status_factor = 1.0
        
        final_confidence = base_confidence * hdop_factor * sat_factor * status_factor
        
        return Confidence(
            value=final_confidence,
            source="gps",
            timestamp_ms=self.timestamp_ms,
            degradation_reason=self._get_degradation_reason()
        )
    
    def _get_degradation_reason(self) -> Optional[str]:
        """Get human-readable degradation reason."""
        reasons = []
        if self.fix_type in ["none", "2D"]:
            reasons.append(f"poor_fix:{self.fix_type}")
        if self.hdop > 2.0:
            reasons.append(f"high_hdop:{self.hdop:.1f}")
        if self.num_satellites < 6:
            reasons.append(f"few_satellites:{self.num_satellites}")
        if self.status != SensorStatus.VALID:
            reasons.append(f"status:{self.status.name}")
        return "; ".join(reasons) if reasons else None
    
    @property
    def is_usable(self) -> bool:
        """Check if this reading can be used at all."""
        return (
            self.status in [SensorStatus.VALID, SensorStatus.STALE, SensorStatus.DEGRADED]
            and self.fix_type not in ["none"]
            and self.num_satellites >= 4
        )


@dataclass(frozen=True)
class GPSVelocity:
    """GPS-derived velocity with uncertainty."""
    
    timestamp_ms: int
    
    # Velocity components (m/s)
    speed_m_s: float
    heading_deg: float  # True heading, 0 = North
    
    # Uncertainty
    speed_accuracy_m_s: float = 1.0
    heading_accuracy_deg: float = 5.0
    
    status: SensorStatus = SensorStatus.VALID
    
    @property
    def speed_kmh(self) -> float:
        """Speed in km/h."""
        return self.speed_m_s * 3.6


@dataclass(frozen=True)
class IMUReading:
    """
    Single IMU reading with accelerometer and gyroscope data.
    
    Coordinate system:
    - X: Forward (positive = acceleration)
    - Y: Right (positive = right turn)
    - Z: Down (positive = compression)
    """
    
    timestamp_ms: int
    
    # Accelerometer (g)
    accel_x_g: float  # Longitudinal
    accel_y_g: float  # Lateral
    accel_z_g: float  # Vertical
    
    # Gyroscope (deg/s)
    gyro_x_dps: float  # Roll rate
    gyro_y_dps: float  # Pitch rate
    gyro_z_dps: float  # Yaw rate
    
    # Temperature (for drift compensation)
    temperature_c: Optional[float] = None
    
    # Status
    status: SensorStatus = SensorStatus.VALID
    
    # Calibration state
    is_calibrated: bool = False
    bias_compensated: bool = False
    
    @property
    def longitudinal_g(self) -> float:
        """Longitudinal acceleration (braking/acceleration)."""
        return self.accel_x_g
    
    @property
    def lateral_g(self) -> float:
        """Lateral acceleration (cornering)."""
        return self.accel_y_g
    
    @property
    def yaw_rate_dps(self) -> float:
        """Yaw rate (rotation around vertical axis)."""
        return self.gyro_z_dps
    
    @property
    def total_g(self) -> float:
        """Total horizontal acceleration magnitude."""
        return math.sqrt(self.accel_x_g**2 + self.accel_y_g**2)
    
    @property
    def confidence(self) -> Confidence:
        """Compute confidence from IMU quality indicators."""
        
        # Check for saturation
        MAX_ACCEL = 8.0  # g
        MAX_GYRO = 500.0  # dps
        
        if (abs(self.accel_x_g) >= MAX_ACCEL or 
            abs(self.accel_y_g) >= MAX_ACCEL or
            abs(self.accel_z_g) >= MAX_ACCEL):
            return Confidence(
                value=0.3,
                source="imu",
                timestamp_ms=self.timestamp_ms,
                degradation_reason="accelerometer_saturated"
            )
        
        if (abs(self.gyro_x_dps) >= MAX_GYRO or
            abs(self.gyro_y_dps) >= MAX_GYRO or
            abs(self.gyro_z_dps) >= MAX_GYRO):
            return Confidence(
                value=0.3,
                source="imu",
                timestamp_ms=self.timestamp_ms,
                degradation_reason="gyroscope_saturated"
            )
        
        # Base confidence
        base = 0.9 if self.is_calibrated else 0.6
        
        # Bias compensation
        if not self.bias_compensated:
            base *= 0.8
        
        # Status check
        if self.status != SensorStatus.VALID:
            base *= 0.5
        
        return Confidence(
            value=base,
            source="imu",
            timestamp_ms=self.timestamp_ms,
            degradation_reason=None if base > 0.8 else "uncalibrated_or_invalid"
        )
    
    @property
    def is_usable(self) -> bool:
        """Check if this reading can be used."""
        return self.status in [SensorStatus.VALID, SensorStatus.STALE, SensorStatus.DEGRADED]


@dataclass(frozen=True)
class FusedPosition:
    """
    Position derived from sensor fusion.
    
    Combines GPS and IMU data with explicit confidence.
    """
    
    timestamp_ms: int
    
    # Position
    latitude_deg: float
    longitude_deg: float
    altitude_m: Optional[float] = None
    
    # Velocity
    speed_m_s: float = 0.0
    heading_deg: float = 0.0
    
    # Acceleration
    longitudinal_g: float = 0.0
    lateral_g: float = 0.0
    
    # Yaw rate
    yaw_rate_dps: float = 0.0
    
    # Confidence
    position_confidence: Confidence = field(default_factory=lambda: Confidence(0.0, "none", 0))
    velocity_confidence: Confidence = field(default_factory=lambda: Confidence(0.0, "none", 0))
    
    # Sources used
    gps_used: bool = False
    imu_used: bool = False
    
    @property
    def overall_confidence(self) -> Confidence:
        """Get minimum confidence across all measurements."""
        return Confidence(
            value=min(self.position_confidence.value, self.velocity_confidence.value),
            source="fused",
            timestamp_ms=self.timestamp_ms,
            degradation_reason=self.position_confidence.degradation_reason or self.velocity_confidence.degradation_reason
        )
    
    @property
    def speed_kmh(self) -> float:
        """Speed in km/h."""
        return self.speed_m_s * 3.6


@dataclass
class TelemetryFrame:
    """
    Complete telemetry frame with all sensor data.
    
    This is the primary data structure passed through the pipeline.
    """
    
    timestamp_ms: int
    
    # Raw sensor data
    gps: Optional[GPSReading] = None
    gps_velocity: Optional[GPSVelocity] = None
    imu: Optional[IMUReading] = None
    
    # Fused data
    fused: Optional[FusedPosition] = None
    
    # Frame metadata
    frame_number: int = 0
    session_id: str = ""
    
    @property
    def has_gps(self) -> bool:
        """Check if GPS data is available and usable."""
        return self.gps is not None and self.gps.is_usable
    
    @property
    def has_imu(self) -> bool:
        """Check if IMU data is available and usable."""
        return self.imu is not None and self.imu.is_usable
    
    @property
    def has_fused(self) -> bool:
        """Check if fused data is available."""
        return self.fused is not None
    
    @property
    def overall_confidence(self) -> Confidence:
        """Get overall telemetry confidence."""
        confidences = []
        
        if self.gps:
            confidences.append(self.gps.confidence)
        if self.imu:
            confidences.append(self.imu.confidence)
        if self.fused:
            confidences.append(self.fused.overall_confidence)
        
        if not confidences:
            return Confidence(
                value=0.0,
                source="telemetry",
                timestamp_ms=self.timestamp_ms,
                degradation_reason="no_sensor_data"
            )
        
        # Use minimum confidence (most conservative)
        min_conf = min(confidences, key=lambda c: c.value)
        return Confidence(
            value=min_conf.value,
            source="telemetry",
            timestamp_ms=self.timestamp_ms,
            degradation_reason=min_conf.degradation_reason
        )


@dataclass
class LapData:
    """
    Collection of telemetry frames for a complete lap.
    """
    
    lap_number: int
    session_id: str
    track_id: str
    
    frames: List[TelemetryFrame] = field(default_factory=list)
    
    # Lap timing
    start_timestamp_ms: int = 0
    end_timestamp_ms: int = 0
    lap_time_ms: int = 0
    
    # Lap validity
    is_complete: bool = False
    is_valid: bool = False
    invalidation_reason: Optional[str] = None
    
    def add_frame(self, frame: TelemetryFrame) -> None:
        """Add a telemetry frame to the lap."""
        self.frames.append(frame)
        
        if not self.start_timestamp_ms:
            self.start_timestamp_ms = frame.timestamp_ms
        self.end_timestamp_ms = frame.timestamp_ms
        self.lap_time_ms = self.end_timestamp_ms - self.start_timestamp_ms
    
    @property
    def frame_count(self) -> int:
        """Number of frames in lap."""
        return len(self.frames)
    
    @property
    def average_confidence(self) -> float:
        """Average confidence across all frames."""
        if not self.frames:
            return 0.0
        return sum(f.overall_confidence.value for f in self.frames) / len(self.frames)
    
    @property
    def minimum_confidence(self) -> float:
        """Minimum confidence in any frame."""
        if not self.frames:
            return 0.0
        return min(f.overall_confidence.value for f in self.frames)
