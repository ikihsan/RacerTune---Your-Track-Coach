"""
Sensor Disagreement Detection
Safety-Critical Adaptive AI Race Coaching System

Detects when GPS and IMU provide inconsistent information.

SAFETY: Sensor disagreement triggers confidence reduction.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import math

from ..types.telemetry import GPSReading, IMUReading, FusedPosition
from ..types.confidence import Confidence


@dataclass
class DisagreementConfig:
    """Configuration for disagreement detection."""
    
    # Speed disagreement thresholds
    speed_disagreement_threshold_m_s: float = 5.0
    
    # Heading disagreement thresholds
    heading_disagreement_threshold_deg: float = 15.0
    
    # Acceleration vs speed change disagreement
    accel_speed_disagreement_threshold: float = 0.3  # g
    
    # Lateral acceleration vs heading change
    lateral_heading_disagreement_threshold: float = 0.2  # g
    
    # History for trend detection
    history_size: int = 10
    
    # Disagreement persistence threshold
    disagreement_count_threshold: int = 3


@dataclass
class DisagreementEvent:
    """Record of a detected disagreement."""
    
    timestamp_ms: int
    disagreement_type: str
    gps_value: float
    imu_value: float
    expected_value: float
    deviation: float


class DisagreementDetector:
    """
    Detects disagreements between GPS and IMU sensors.
    
    Disagreement indicates one or both sensors are providing
    incorrect data. This should trigger confidence reduction.
    
    SAFETY: 
    - Persistent disagreement indicates sensor problems
    - Use lower/safer estimate when disagreement detected
    """
    
    def __init__(self, config: Optional[DisagreementConfig] = None):
        self.config = config or DisagreementConfig()
        
        # State
        self._history: List[DisagreementEvent] = []
        self._last_gps: Optional[GPSReading] = None
        self._last_fused: Optional[FusedPosition] = None
        self._disagreement_count: int = 0
        
    def check(
        self,
        gps: GPSReading,
        gps_confidence: Confidence,
        imu: IMUReading,
        imu_confidence: Confidence,
        fused: FusedPosition
    ) -> bool:
        """
        Check for disagreement between sensors.
        
        Args:
            gps: Current GPS reading
            gps_confidence: GPS confidence
            imu: Current IMU reading
            imu_confidence: IMU confidence
            fused: Current fused position
            
        Returns:
            True if significant disagreement detected
        """
        disagreements = []
        
        # Check acceleration vs speed change
        if self._last_fused:
            accel_disagreement = self._check_acceleration_speed(
                imu, fused, self._last_fused
            )
            if accel_disagreement:
                disagreements.append(accel_disagreement)
        
        # Check lateral acceleration vs heading change
        if self._last_fused:
            lateral_disagreement = self._check_lateral_heading(
                imu, fused, self._last_fused
            )
            if lateral_disagreement:
                disagreements.append(lateral_disagreement)
        
        # Check yaw rate vs GPS heading change
        if self._last_gps:
            yaw_disagreement = self._check_yaw_heading(
                imu, gps, self._last_gps
            )
            if yaw_disagreement:
                disagreements.append(yaw_disagreement)
        
        # Update state
        self._last_gps = gps
        self._last_fused = fused
        
        # Record disagreements
        for event in disagreements:
            self._record_disagreement(event)
        
        # Update disagreement count
        if disagreements:
            self._disagreement_count += 1
        else:
            self._disagreement_count = max(0, self._disagreement_count - 1)
        
        # Return True if persistent disagreement
        return self._disagreement_count >= self.config.disagreement_count_threshold
    
    def _check_acceleration_speed(
        self,
        imu: IMUReading,
        current_fused: FusedPosition,
        last_fused: FusedPosition
    ) -> Optional[DisagreementEvent]:
        """
        Check if IMU acceleration matches GPS speed change.
        
        If we're accelerating according to IMU, speed should increase.
        """
        dt_s = (current_fused.timestamp_ms - last_fused.timestamp_ms) / 1000.0
        
        if dt_s <= 0:
            return None
        
        # Compute speed change from GPS
        gps_speed_change = current_fused.speed_m_s - last_fused.speed_m_s
        gps_accel = gps_speed_change / dt_s  # m/s^2
        gps_accel_g = gps_accel / 9.81
        
        # Get IMU longitudinal acceleration
        imu_accel_g = imu.longitudinal_g
        
        # Compare
        deviation = abs(gps_accel_g - imu_accel_g)
        
        if deviation > self.config.accel_speed_disagreement_threshold:
            return DisagreementEvent(
                timestamp_ms=current_fused.timestamp_ms,
                disagreement_type="acceleration_speed",
                gps_value=gps_accel_g,
                imu_value=imu_accel_g,
                expected_value=gps_accel_g,  # GPS is reference
                deviation=deviation
            )
        
        return None
    
    def _check_lateral_heading(
        self,
        imu: IMUReading,
        current_fused: FusedPosition,
        last_fused: FusedPosition
    ) -> Optional[DisagreementEvent]:
        """
        Check if IMU lateral acceleration matches heading change.
        
        If we're cornering according to IMU, heading should change.
        """
        dt_s = (current_fused.timestamp_ms - last_fused.timestamp_ms) / 1000.0
        
        if dt_s <= 0 or current_fused.speed_m_s < 5.0:  # Need some speed
            return None
        
        # Compute heading change rate from GPS
        heading_change = current_fused.heading_deg - last_fused.heading_deg
        
        # Normalize to -180 to 180
        while heading_change > 180:
            heading_change -= 360
        while heading_change < -180:
            heading_change += 360
        
        heading_rate_dps = heading_change / dt_s
        
        # Expected lateral acceleration: a = v * omega
        # omega in rad/s: heading_rate_dps * pi / 180
        omega_rad_s = heading_rate_dps * math.pi / 180
        expected_lateral_m_s2 = current_fused.speed_m_s * omega_rad_s
        expected_lateral_g = expected_lateral_m_s2 / 9.81
        
        # Get IMU lateral acceleration
        imu_lateral_g = imu.lateral_g
        
        # Compare
        deviation = abs(expected_lateral_g - imu_lateral_g)
        
        if deviation > self.config.lateral_heading_disagreement_threshold:
            return DisagreementEvent(
                timestamp_ms=current_fused.timestamp_ms,
                disagreement_type="lateral_heading",
                gps_value=expected_lateral_g,
                imu_value=imu_lateral_g,
                expected_value=expected_lateral_g,
                deviation=deviation
            )
        
        return None
    
    def _check_yaw_heading(
        self,
        imu: IMUReading,
        current_gps: GPSReading,
        last_gps: GPSReading
    ) -> Optional[DisagreementEvent]:
        """
        Check if IMU yaw rate matches GPS heading change.
        """
        dt_s = (current_gps.timestamp_ms - last_gps.timestamp_ms) / 1000.0
        
        if dt_s <= 0:
            return None
        
        # Compute heading change from GPS position
        heading = math.degrees(math.atan2(
            current_gps.longitude_deg - last_gps.longitude_deg,
            current_gps.latitude_deg - last_gps.latitude_deg
        ))
        
        last_heading = math.degrees(math.atan2(
            last_gps.longitude_deg - (last_gps.longitude_deg - 0.0001),
            last_gps.latitude_deg - (last_gps.latitude_deg - 0.0001)
        ))
        
        # This is a rough estimate and may not be reliable for slow speeds
        # Skip comparison if speed is too low
        
        return None  # Simplified - full implementation would compare yaw rates
    
    def _record_disagreement(self, event: DisagreementEvent) -> None:
        """Record a disagreement event."""
        self._history.append(event)
        
        if len(self._history) > self.config.history_size:
            self._history.pop(0)
    
    def get_disagreement_rate(self) -> float:
        """Get the rate of disagreement over recent history."""
        if not self._history:
            return 0.0
        
        return len(self._history) / self.config.history_size
    
    def get_dominant_disagreement_type(self) -> Optional[str]:
        """Get the most common type of disagreement."""
        if not self._history:
            return None
        
        type_counts: dict = {}
        for event in self._history:
            type_counts[event.disagreement_type] = type_counts.get(event.disagreement_type, 0) + 1
        
        if type_counts:
            return max(type_counts, key=type_counts.get)
        
        return None
    
    def reset(self) -> None:
        """Reset detector state."""
        self._history.clear()
        self._last_gps = None
        self._last_fused = None
        self._disagreement_count = 0
