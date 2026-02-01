"""
GPS Processor
Safety-Critical Adaptive AI Race Coaching System

Processes GPS data with explicit noise modeling and quality assessment.

SAFETY: Never assumes GPS data is accurate. Always propagates uncertainty.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import math

from ..types.telemetry import GPSReading, GPSVelocity, SensorStatus
from ..types.confidence import Confidence


@dataclass
class GPSConfig:
    """Configuration for GPS processing."""
    
    # Quality thresholds
    min_satellites: int = 6
    max_hdop: float = 2.0
    max_position_age_ms: int = 500
    
    # Noise model
    base_horizontal_noise_m: float = 2.0  # Typical GPS noise
    hdop_noise_multiplier: float = 1.5     # Noise scales with HDOP
    
    # Outlier detection
    max_speed_m_s: float = 100.0           # ~360 km/h
    max_position_jump_m: float = 20.0      # Per update
    max_heading_change_deg: float = 45.0   # Per update
    
    # Dropout handling
    max_dropout_duration_ms: int = 2000
    
    # Jitter filtering
    jitter_filter_samples: int = 3
    jitter_threshold_m: float = 1.0


class GPSProcessor:
    """
    Processes GPS readings with quality assessment and noise modeling.
    
    SAFETY INVARIANT: 
    - GPS confidence reflects actual measurement quality
    - Dropouts and poor quality are explicitly flagged
    - No assumptions of GPS accuracy
    """
    
    def __init__(self, config: Optional[GPSConfig] = None):
        self.config = config or GPSConfig()
        
        # State for processing
        self._last_valid_reading: Optional[GPSReading] = None
        self._last_valid_velocity: Optional[GPSVelocity] = None
        self._recent_readings: List[GPSReading] = []
        self._dropout_start_ms: Optional[int] = None
        
    def process(self, reading: GPSReading) -> Tuple[GPSReading, Confidence]:
        """
        Process a GPS reading with quality assessment.
        
        Args:
            reading: Raw GPS reading
            
        Returns:
            Tuple of (processed reading, confidence)
        """
        # Check for invalid reading
        if not self._is_valid_reading(reading):
            return self._handle_invalid_reading(reading)
        
        # Check for outliers
        if self._is_outlier(reading):
            return self._handle_outlier(reading)
        
        # Apply jitter filtering
        filtered = self._apply_jitter_filter(reading)
        
        # Compute confidence
        confidence = self._compute_confidence(filtered)
        
        # Update state
        self._update_state(filtered)
        
        return filtered, confidence
    
    def _is_valid_reading(self, reading: GPSReading) -> bool:
        """Check if reading meets minimum validity requirements."""
        
        if reading.status == SensorStatus.INVALID:
            return False
        
        if reading.fix_type == "none":
            return False
        
        if reading.num_satellites < 4:
            return False
        
        # Check for NaN or invalid coordinates
        if math.isnan(reading.latitude_deg) or math.isnan(reading.longitude_deg):
            return False
        
        if not -90 <= reading.latitude_deg <= 90:
            return False
        
        if not -180 <= reading.longitude_deg <= 180:
            return False
        
        return True
    
    def _is_outlier(self, reading: GPSReading) -> bool:
        """Detect outlier readings based on physics constraints."""
        
        if self._last_valid_reading is None:
            return False  # First reading cannot be outlier
        
        # Compute distance from last valid position
        distance = self._haversine_distance(
            self._last_valid_reading.latitude_deg,
            self._last_valid_reading.longitude_deg,
            reading.latitude_deg,
            reading.longitude_deg
        )
        
        # Compute time delta
        dt_ms = reading.timestamp_ms - self._last_valid_reading.timestamp_ms
        dt_s = dt_ms / 1000.0
        
        if dt_s <= 0:
            return True  # Invalid timestamp
        
        # Check speed implied by position change
        implied_speed_m_s = distance / dt_s
        
        if implied_speed_m_s > self.config.max_speed_m_s:
            return True  # Impossible speed
        
        # Check for unreasonable position jump
        if distance > self.config.max_position_jump_m and dt_s < 1.0:
            return True
        
        return False
    
    def _apply_jitter_filter(self, reading: GPSReading) -> GPSReading:
        """Apply simple jitter filtering."""
        
        self._recent_readings.append(reading)
        
        if len(self._recent_readings) > self.config.jitter_filter_samples:
            self._recent_readings.pop(0)
        
        if len(self._recent_readings) < self.config.jitter_filter_samples:
            return reading  # Not enough samples yet
        
        # Check if readings are within jitter threshold
        lat_spread = max(r.latitude_deg for r in self._recent_readings) - \
                     min(r.latitude_deg for r in self._recent_readings)
        lon_spread = max(r.longitude_deg for r in self._recent_readings) - \
                     min(r.longitude_deg for r in self._recent_readings)
        
        # Convert to approximate meters
        lat_spread_m = lat_spread * 111000
        lon_spread_m = lon_spread * 111000 * math.cos(math.radians(reading.latitude_deg))
        
        spread_m = math.sqrt(lat_spread_m**2 + lon_spread_m**2)
        
        if spread_m < self.config.jitter_threshold_m:
            # Average the readings to reduce jitter
            avg_lat = sum(r.latitude_deg for r in self._recent_readings) / len(self._recent_readings)
            avg_lon = sum(r.longitude_deg for r in self._recent_readings) / len(self._recent_readings)
            
            return GPSReading(
                timestamp_ms=reading.timestamp_ms,
                latitude_deg=avg_lat,
                longitude_deg=avg_lon,
                altitude_m=reading.altitude_m,
                horizontal_accuracy_m=reading.horizontal_accuracy_m,
                vertical_accuracy_m=reading.vertical_accuracy_m,
                hdop=reading.hdop,
                num_satellites=reading.num_satellites,
                fix_type=reading.fix_type,
                status=reading.status
            )
        
        return reading
    
    def _compute_confidence(self, reading: GPSReading) -> Confidence:
        """Compute confidence score for GPS reading."""
        
        # Start with base confidence from reading
        base = reading.confidence.value
        
        # Adjust for HDOP
        if reading.hdop > self.config.max_hdop:
            hdop_factor = self.config.max_hdop / reading.hdop
        else:
            hdop_factor = 1.0
        
        # Adjust for satellite count
        sat_deficit = self.config.min_satellites - reading.num_satellites
        if sat_deficit > 0:
            sat_factor = max(0.5, 1.0 - sat_deficit * 0.1)
        else:
            sat_factor = 1.0
        
        # Combine factors
        final_confidence = base * hdop_factor * sat_factor
        
        # Build degradation reason
        reasons = []
        if hdop_factor < 1.0:
            reasons.append(f"hdop:{reading.hdop:.1f}")
        if sat_factor < 1.0:
            reasons.append(f"satellites:{reading.num_satellites}")
        
        return Confidence(
            value=final_confidence,
            source="gps_processor",
            timestamp_ms=reading.timestamp_ms,
            degradation_reason="; ".join(reasons) if reasons else None
        )
    
    def _handle_invalid_reading(
        self,
        reading: GPSReading
    ) -> Tuple[GPSReading, Confidence]:
        """Handle invalid GPS reading."""
        
        # Track dropout duration
        if self._dropout_start_ms is None:
            self._dropout_start_ms = reading.timestamp_ms
        
        dropout_duration = reading.timestamp_ms - self._dropout_start_ms
        
        # Return last valid reading with degraded confidence if available
        if self._last_valid_reading and dropout_duration < self.config.max_dropout_duration_ms:
            # Confidence degrades with dropout duration
            degradation = 1.0 - (dropout_duration / self.config.max_dropout_duration_ms)
            
            return self._last_valid_reading, Confidence(
                value=degradation * 0.5,  # Max 50% confidence during dropout
                source="gps_dropout",
                timestamp_ms=reading.timestamp_ms,
                degradation_reason=f"dropout:{dropout_duration}ms"
            )
        
        # No valid reading available
        return reading, Confidence(
            value=0.0,
            source="gps_invalid",
            timestamp_ms=reading.timestamp_ms,
            degradation_reason="no_valid_gps"
        )
    
    def _handle_outlier(
        self,
        reading: GPSReading
    ) -> Tuple[GPSReading, Confidence]:
        """Handle outlier GPS reading."""
        
        # Return last valid reading with reduced confidence
        if self._last_valid_reading:
            return self._last_valid_reading, Confidence(
                value=0.4,
                source="gps_outlier_rejected",
                timestamp_ms=reading.timestamp_ms,
                degradation_reason="outlier_detected"
            )
        
        # Accept with very low confidence if no alternative
        return reading, Confidence(
            value=0.2,
            source="gps_outlier_forced",
            timestamp_ms=reading.timestamp_ms,
            degradation_reason="outlier_no_alternative"
        )
    
    def _update_state(self, reading: GPSReading) -> None:
        """Update processor state with valid reading."""
        self._last_valid_reading = reading
        self._dropout_start_ms = None  # Reset dropout tracking
    
    def compute_velocity(
        self,
        reading: GPSReading,
        previous: GPSReading
    ) -> Optional[GPSVelocity]:
        """Compute velocity from position change."""
        
        dt_ms = reading.timestamp_ms - previous.timestamp_ms
        if dt_ms <= 0:
            return None
        
        dt_s = dt_ms / 1000.0
        
        # Compute distance
        distance = self._haversine_distance(
            previous.latitude_deg,
            previous.longitude_deg,
            reading.latitude_deg,
            reading.longitude_deg
        )
        
        # Compute speed
        speed_m_s = distance / dt_s
        
        # Compute heading
        heading = self._compute_heading(
            previous.latitude_deg,
            previous.longitude_deg,
            reading.latitude_deg,
            reading.longitude_deg
        )
        
        # Estimate accuracy based on position accuracy and time delta
        speed_accuracy = (reading.horizontal_accuracy_m + previous.horizontal_accuracy_m) / dt_s
        
        return GPSVelocity(
            timestamp_ms=reading.timestamp_ms,
            speed_m_s=speed_m_s,
            heading_deg=heading,
            speed_accuracy_m_s=speed_accuracy,
            heading_accuracy_deg=10.0  # Estimate
        )
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Compute distance between two GPS coordinates in meters."""
        
        R = 6371000  # Earth radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def _compute_heading(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Compute heading from point 1 to point 2 in degrees."""
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_lambda = math.radians(lon2 - lon1)
        
        x = math.sin(delta_lambda) * math.cos(phi2)
        y = (math.cos(phi1) * math.sin(phi2) -
             math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda))
        
        heading = math.degrees(math.atan2(x, y))
        
        return (heading + 360) % 360  # Normalize to 0-360
    
    def reset(self) -> None:
        """Reset processor state."""
        self._last_valid_reading = None
        self._last_valid_velocity = None
        self._recent_readings.clear()
        self._dropout_start_ms = None
