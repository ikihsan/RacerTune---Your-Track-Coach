"""
Sensor Fusion Engine
Safety-Critical Adaptive AI Race Coaching System

Fuses GPS and IMU data with confidence-weighted blending.

SAFETY: 
- No assumptions of ideal sensors
- Confidence propagates through fusion
- Sensor disagreement triggers degradation
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import math

from ..types.telemetry import (
    GPSReading, GPSVelocity, IMUReading, FusedPosition, TelemetryFrame
)
from ..types.confidence import Confidence, fuse_confidence
from .gps_processor import GPSProcessor
from .imu_processor import IMUProcessor
from .disagreement import DisagreementDetector


@dataclass
class FusionConfig:
    """Configuration for sensor fusion."""
    
    # Fusion weights
    gps_position_weight: float = 0.7
    imu_position_weight: float = 0.3  # Dead reckoning contribution
    
    # Update rates
    fusion_rate_hz: float = 50.0
    gps_rate_hz: float = 10.0
    
    # Confidence thresholds
    min_fusion_confidence: float = 0.3
    disagreement_threshold: float = 0.3
    
    # Dead reckoning limits
    max_dead_reckoning_duration_ms: int = 2000
    dead_reckoning_confidence_decay: float = 0.9  # Per 100ms


class SensorFusionEngine:
    """
    Fuses GPS and IMU data into a unified state estimate.
    
    Uses a simplified complementary filter approach:
    - GPS provides low-frequency position/velocity updates
    - IMU provides high-frequency local updates
    - Confidence weighting ensures degraded sensors have less influence
    
    SAFETY INVARIANT:
    - Fusion confidence reflects the weakest input
    - Disagreement between sensors triggers confidence reduction
    - Dead reckoning has time-limited validity
    """
    
    def __init__(
        self,
        config: Optional[FusionConfig] = None,
        gps_processor: Optional[GPSProcessor] = None,
        imu_processor: Optional[IMUProcessor] = None
    ):
        self.config = config or FusionConfig()
        self.gps_processor = gps_processor or GPSProcessor()
        self.imu_processor = imu_processor or IMUProcessor()
        self.disagreement_detector = DisagreementDetector()
        
        # State
        self._last_fused: Optional[FusedPosition] = None
        self._last_gps: Optional[GPSReading] = None
        self._last_gps_confidence: Optional[Confidence] = None
        self._last_gps_time_ms: int = 0
        
        # Dead reckoning state
        self._dead_reckoning_active: bool = False
        self._dead_reckoning_start_ms: int = 0
        
    def process_frame(self, frame: TelemetryFrame) -> TelemetryFrame:
        """
        Process a telemetry frame through sensor fusion.
        
        Args:
            frame: Input telemetry frame with raw sensor data
            
        Returns:
            Frame with fused position added
        """
        gps_result = None
        gps_confidence = None
        imu_result = None
        imu_confidence = None
        
        # Process GPS if available
        if frame.gps:
            gps_result, gps_confidence = self.gps_processor.process(frame.gps)
            
            if gps_confidence.value > 0.3:
                self._last_gps = gps_result
                self._last_gps_confidence = gps_confidence
                self._last_gps_time_ms = frame.timestamp_ms
                self._dead_reckoning_active = False
        
        # Process IMU if available
        if frame.imu:
            imu_result, imu_confidence = self.imu_processor.process(frame.imu)
        
        # Perform fusion
        fused = self._fuse_sensors(
            frame.timestamp_ms,
            gps_result,
            gps_confidence,
            frame.gps_velocity,
            imu_result,
            imu_confidence
        )
        
        # Check for disagreement
        if gps_result and imu_result and gps_confidence and imu_confidence:
            disagreement = self.disagreement_detector.check(
                gps_result,
                gps_confidence,
                imu_result,
                imu_confidence,
                fused
            )
            
            if disagreement:
                # Reduce confidence due to disagreement
                fused = FusedPosition(
                    timestamp_ms=fused.timestamp_ms,
                    latitude_deg=fused.latitude_deg,
                    longitude_deg=fused.longitude_deg,
                    altitude_m=fused.altitude_m,
                    speed_m_s=fused.speed_m_s,
                    heading_deg=fused.heading_deg,
                    longitudinal_g=fused.longitudinal_g,
                    lateral_g=fused.lateral_g,
                    yaw_rate_dps=fused.yaw_rate_dps,
                    position_confidence=fused.position_confidence.degrade(
                        0.7, "sensor_disagreement"
                    ),
                    velocity_confidence=fused.velocity_confidence.degrade(
                        0.7, "sensor_disagreement"
                    ),
                    gps_used=fused.gps_used,
                    imu_used=fused.imu_used
                )
        
        # Update state
        self._last_fused = fused
        
        # Return updated frame
        frame.fused = fused
        return frame
    
    def _fuse_sensors(
        self,
        timestamp_ms: int,
        gps: Optional[GPSReading],
        gps_confidence: Optional[Confidence],
        gps_velocity: Optional[GPSVelocity],
        imu: Optional[IMUReading],
        imu_confidence: Optional[Confidence]
    ) -> FusedPosition:
        """
        Perform sensor fusion.
        
        Strategy:
        1. If GPS available and confident, use as position base
        2. Add IMU for acceleration and yaw rate
        3. If GPS unavailable, use dead reckoning from IMU
        4. Confidence reflects fusion quality
        """
        
        has_gps = gps is not None and gps_confidence is not None and gps_confidence.value > 0.3
        has_imu = imu is not None and imu_confidence is not None and imu_confidence.value > 0.3
        
        # Case 1: Both sensors available
        if has_gps and has_imu:
            return self._fuse_both(
                timestamp_ms, gps, gps_confidence, gps_velocity, imu, imu_confidence
            )
        
        # Case 2: GPS only
        if has_gps:
            return self._fuse_gps_only(timestamp_ms, gps, gps_confidence, gps_velocity)
        
        # Case 3: IMU only (dead reckoning)
        if has_imu:
            return self._dead_reckon(timestamp_ms, imu, imu_confidence)
        
        # Case 4: No valid sensors
        return self._no_sensors(timestamp_ms)
    
    def _fuse_both(
        self,
        timestamp_ms: int,
        gps: GPSReading,
        gps_confidence: Confidence,
        gps_velocity: Optional[GPSVelocity],
        imu: IMUReading,
        imu_confidence: Confidence
    ) -> FusedPosition:
        """Fuse GPS and IMU when both available."""
        
        # Position from GPS
        latitude = gps.latitude_deg
        longitude = gps.longitude_deg
        altitude = gps.altitude_m
        
        # Velocity from GPS velocity if available, otherwise from position difference
        if gps_velocity:
            speed = gps_velocity.speed_m_s
            heading = gps_velocity.heading_deg
        elif self._last_gps:
            # Compute velocity from position change
            velocity = self.gps_processor.compute_velocity(gps, self._last_gps)
            if velocity:
                speed = velocity.speed_m_s
                heading = velocity.heading_deg
            else:
                speed = 0.0
                heading = 0.0
        else:
            speed = 0.0
            heading = 0.0
        
        # Acceleration from IMU (already processed)
        longitudinal_g = imu.longitudinal_g
        lateral_g = imu.lateral_g
        yaw_rate = imu.yaw_rate_dps
        
        # Fuse confidence
        position_conf = gps_confidence  # Position primarily from GPS
        velocity_conf = fuse_confidence(
            [gps_confidence, imu_confidence],
            method="minimum"
        )
        
        return FusedPosition(
            timestamp_ms=timestamp_ms,
            latitude_deg=latitude,
            longitude_deg=longitude,
            altitude_m=altitude,
            speed_m_s=speed,
            heading_deg=heading,
            longitudinal_g=longitudinal_g,
            lateral_g=lateral_g,
            yaw_rate_dps=yaw_rate,
            position_confidence=position_conf,
            velocity_confidence=velocity_conf,
            gps_used=True,
            imu_used=True
        )
    
    def _fuse_gps_only(
        self,
        timestamp_ms: int,
        gps: GPSReading,
        gps_confidence: Confidence,
        gps_velocity: Optional[GPSVelocity]
    ) -> FusedPosition:
        """Fuse with GPS only (no IMU)."""
        
        if gps_velocity:
            speed = gps_velocity.speed_m_s
            heading = gps_velocity.heading_deg
        else:
            speed = 0.0
            heading = 0.0
        
        # Degraded confidence without IMU
        degraded_conf = gps_confidence.degrade(0.8, "no_imu")
        
        return FusedPosition(
            timestamp_ms=timestamp_ms,
            latitude_deg=gps.latitude_deg,
            longitude_deg=gps.longitude_deg,
            altitude_m=gps.altitude_m,
            speed_m_s=speed,
            heading_deg=heading,
            longitudinal_g=0.0,
            lateral_g=0.0,
            yaw_rate_dps=0.0,
            position_confidence=degraded_conf,
            velocity_confidence=degraded_conf,
            gps_used=True,
            imu_used=False
        )
    
    def _dead_reckon(
        self,
        timestamp_ms: int,
        imu: IMUReading,
        imu_confidence: Confidence
    ) -> FusedPosition:
        """Dead reckon from last known position using IMU."""
        
        if not self._dead_reckoning_active:
            self._dead_reckoning_active = True
            self._dead_reckoning_start_ms = timestamp_ms
        
        # Check dead reckoning duration
        dr_duration_ms = timestamp_ms - self._dead_reckoning_start_ms
        
        if dr_duration_ms > self.config.max_dead_reckoning_duration_ms:
            # Dead reckoning expired - very low confidence
            return self._no_sensors(timestamp_ms)
        
        # Decay confidence with time
        decay_periods = dr_duration_ms / 100.0
        dr_confidence = imu_confidence.value * (
            self.config.dead_reckoning_confidence_decay ** decay_periods
        )
        
        # Use last known position (if available)
        if self._last_fused:
            # Simple dead reckoning: assume constant velocity
            dt_s = (timestamp_ms - self._last_fused.timestamp_ms) / 1000.0
            
            # Integrate acceleration to update velocity (simplified)
            # This is very approximate and drifts quickly
            
            return FusedPosition(
                timestamp_ms=timestamp_ms,
                latitude_deg=self._last_fused.latitude_deg,
                longitude_deg=self._last_fused.longitude_deg,
                altitude_m=self._last_fused.altitude_m,
                speed_m_s=self._last_fused.speed_m_s,
                heading_deg=self._last_fused.heading_deg,
                longitudinal_g=imu.longitudinal_g,
                lateral_g=imu.lateral_g,
                yaw_rate_dps=imu.yaw_rate_dps,
                position_confidence=Confidence(
                    value=dr_confidence * 0.5,  # Position very uncertain
                    source="dead_reckoning",
                    timestamp_ms=timestamp_ms,
                    degradation_reason=f"dr_duration:{dr_duration_ms}ms"
                ),
                velocity_confidence=Confidence(
                    value=dr_confidence,
                    source="dead_reckoning",
                    timestamp_ms=timestamp_ms,
                    degradation_reason=f"dr_duration:{dr_duration_ms}ms"
                ),
                gps_used=False,
                imu_used=True
            )
        
        # No previous position - can only provide IMU data
        return FusedPosition(
            timestamp_ms=timestamp_ms,
            latitude_deg=0.0,
            longitude_deg=0.0,
            altitude_m=None,
            speed_m_s=0.0,
            heading_deg=0.0,
            longitudinal_g=imu.longitudinal_g,
            lateral_g=imu.lateral_g,
            yaw_rate_dps=imu.yaw_rate_dps,
            position_confidence=Confidence(
                value=0.0,
                source="dead_reckoning",
                timestamp_ms=timestamp_ms,
                degradation_reason="no_initial_position"
            ),
            velocity_confidence=Confidence(
                value=dr_confidence * 0.5,
                source="dead_reckoning",
                timestamp_ms=timestamp_ms,
                degradation_reason="no_initial_position"
            ),
            gps_used=False,
            imu_used=True
        )
    
    def _no_sensors(self, timestamp_ms: int) -> FusedPosition:
        """Handle case with no valid sensor data."""
        
        return FusedPosition(
            timestamp_ms=timestamp_ms,
            latitude_deg=0.0,
            longitude_deg=0.0,
            altitude_m=None,
            speed_m_s=0.0,
            heading_deg=0.0,
            longitudinal_g=0.0,
            lateral_g=0.0,
            yaw_rate_dps=0.0,
            position_confidence=Confidence(
                value=0.0,
                source="no_sensors",
                timestamp_ms=timestamp_ms,
                degradation_reason="no_valid_sensor_data"
            ),
            velocity_confidence=Confidence(
                value=0.0,
                source="no_sensors",
                timestamp_ms=timestamp_ms,
                degradation_reason="no_valid_sensor_data"
            ),
            gps_used=False,
            imu_used=False
        )
    
    def get_state(self) -> dict:
        """Get current fusion state for diagnostics."""
        return {
            "has_valid_gps": self._last_gps is not None,
            "gps_confidence": self._last_gps_confidence.value if self._last_gps_confidence else 0.0,
            "dead_reckoning_active": self._dead_reckoning_active,
            "dead_reckoning_duration_ms": (
                0 if not self._dead_reckoning_active else
                (self._last_fused.timestamp_ms if self._last_fused else 0) - self._dead_reckoning_start_ms
            ),
            "last_fused_confidence": (
                self._last_fused.overall_confidence.value if self._last_fused else 0.0
            )
        }
    
    def reset(self) -> None:
        """Reset fusion state."""
        self._last_fused = None
        self._last_gps = None
        self._last_gps_confidence = None
        self._last_gps_time_ms = 0
        self._dead_reckoning_active = False
        self._dead_reckoning_start_ms = 0
        self.gps_processor.reset()
        self.imu_processor.reset()
        self.disagreement_detector.reset()
