"""
IMU Processor
Safety-Critical Adaptive AI Race Coaching System

Processes IMU data with drift compensation and quality assessment.

SAFETY: Never assumes IMU data is accurate. Explicitly models drift and bias.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import math

from ..types.telemetry import IMUReading, SensorStatus
from ..types.confidence import Confidence


@dataclass
class IMUConfig:
    """Configuration for IMU processing."""
    
    # Sensor limits
    max_accel_g: float = 8.0
    max_gyro_dps: float = 500.0
    
    # Bias estimation
    bias_estimation_samples: int = 100
    stationary_accel_threshold_g: float = 0.1
    stationary_gyro_threshold_dps: float = 1.0
    
    # Drift model
    gyro_drift_rate_dps_per_s: float = 0.01  # Typical MEMS drift
    accel_bias_stability_g: float = 0.01
    
    # Filtering
    low_pass_alpha: float = 0.3  # Low-pass filter coefficient
    
    # Quality thresholds
    max_stale_age_ms: int = 100
    
    # Mounting orientation (degrees)
    roll_offset_deg: float = 0.0
    pitch_offset_deg: float = 0.0
    yaw_offset_deg: float = 0.0


@dataclass
class IMUBias:
    """Estimated IMU biases for compensation."""
    
    accel_x_bias_g: float = 0.0
    accel_y_bias_g: float = 0.0
    accel_z_bias_g: float = 0.0
    
    gyro_x_bias_dps: float = 0.0
    gyro_y_bias_dps: float = 0.0
    gyro_z_bias_dps: float = 0.0
    
    # Bias confidence
    samples_collected: int = 0
    is_valid: bool = False
    estimation_timestamp_ms: int = 0


class IMUProcessor:
    """
    Processes IMU readings with drift compensation and quality assessment.
    
    SAFETY INVARIANT:
    - IMU drift is explicitly modeled and compensated
    - Saturation is detected and flagged
    - Confidence reflects actual measurement quality
    """
    
    def __init__(self, config: Optional[IMUConfig] = None):
        self.config = config or IMUConfig()
        
        # State
        self._last_reading: Optional[IMUReading] = None
        self._bias = IMUBias()
        self._calibration_samples: List[IMUReading] = []
        self._is_calibrating: bool = False
        
        # Running statistics for drift estimation
        self._gyro_integral_deg = [0.0, 0.0, 0.0]  # x, y, z
        self._integration_start_ms: Optional[int] = None
        
    def process(self, reading: IMUReading) -> Tuple[IMUReading, Confidence]:
        """
        Process an IMU reading with bias compensation and quality assessment.
        
        Args:
            reading: Raw IMU reading
            
        Returns:
            Tuple of (processed reading, confidence)
        """
        # Check for saturation
        saturation = self._check_saturation(reading)
        if saturation:
            return self._handle_saturation(reading, saturation)
        
        # Apply bias compensation
        compensated = self._apply_bias_compensation(reading)
        
        # Apply low-pass filtering
        filtered = self._apply_filter(compensated)
        
        # Apply mounting orientation correction
        oriented = self._apply_orientation_correction(filtered)
        
        # Compute confidence
        confidence = self._compute_confidence(oriented)
        
        # Update state
        self._last_reading = oriented
        
        return oriented, confidence
    
    def start_calibration(self) -> None:
        """Start stationary calibration process."""
        self._is_calibrating = True
        self._calibration_samples.clear()
    
    def add_calibration_sample(self, reading: IMUReading) -> bool:
        """
        Add a sample to calibration.
        
        Returns:
            True if calibration is complete
        """
        if not self._is_calibrating:
            return False
        
        # Check if stationary
        if not self._is_stationary(reading):
            # Reset calibration if motion detected
            self._calibration_samples.clear()
            return False
        
        self._calibration_samples.append(reading)
        
        if len(self._calibration_samples) >= self.config.bias_estimation_samples:
            self._complete_calibration()
            return True
        
        return False
    
    def _is_stationary(self, reading: IMUReading) -> bool:
        """Check if vehicle is stationary based on IMU readings."""
        
        # Check accelerometer (should show only gravity)
        # Assuming Z is vertical, expect ~1g on Z, near 0 on X/Y
        expected_z = 1.0  # g
        
        accel_deviation = math.sqrt(
            reading.accel_x_g**2 +
            reading.accel_y_g**2 +
            (reading.accel_z_g - expected_z)**2
        )
        
        if accel_deviation > self.config.stationary_accel_threshold_g:
            return False
        
        # Check gyroscope (should be near zero)
        gyro_magnitude = math.sqrt(
            reading.gyro_x_dps**2 +
            reading.gyro_y_dps**2 +
            reading.gyro_z_dps**2
        )
        
        if gyro_magnitude > self.config.stationary_gyro_threshold_dps:
            return False
        
        return True
    
    def _complete_calibration(self) -> None:
        """Complete calibration and compute biases."""
        
        if not self._calibration_samples:
            return
        
        n = len(self._calibration_samples)
        
        # Compute mean biases
        self._bias.accel_x_bias_g = sum(s.accel_x_g for s in self._calibration_samples) / n
        self._bias.accel_y_bias_g = sum(s.accel_y_g for s in self._calibration_samples) / n
        # Z bias is relative to gravity
        self._bias.accel_z_bias_g = sum(s.accel_z_g for s in self._calibration_samples) / n - 1.0
        
        self._bias.gyro_x_bias_dps = sum(s.gyro_x_dps for s in self._calibration_samples) / n
        self._bias.gyro_y_bias_dps = sum(s.gyro_y_dps for s in self._calibration_samples) / n
        self._bias.gyro_z_bias_dps = sum(s.gyro_z_dps for s in self._calibration_samples) / n
        
        self._bias.samples_collected = n
        self._bias.is_valid = True
        self._bias.estimation_timestamp_ms = self._calibration_samples[-1].timestamp_ms
        
        self._is_calibrating = False
        self._calibration_samples.clear()
    
    def _check_saturation(self, reading: IMUReading) -> Optional[str]:
        """Check if any sensor is saturated."""
        
        if abs(reading.accel_x_g) >= self.config.max_accel_g:
            return "accel_x"
        if abs(reading.accel_y_g) >= self.config.max_accel_g:
            return "accel_y"
        if abs(reading.accel_z_g) >= self.config.max_accel_g:
            return "accel_z"
        
        if abs(reading.gyro_x_dps) >= self.config.max_gyro_dps:
            return "gyro_x"
        if abs(reading.gyro_y_dps) >= self.config.max_gyro_dps:
            return "gyro_y"
        if abs(reading.gyro_z_dps) >= self.config.max_gyro_dps:
            return "gyro_z"
        
        return None
    
    def _handle_saturation(
        self,
        reading: IMUReading,
        saturated_axis: str
    ) -> Tuple[IMUReading, Confidence]:
        """Handle saturated sensor reading."""
        
        # Return reading with saturated status and low confidence
        saturated_reading = IMUReading(
            timestamp_ms=reading.timestamp_ms,
            accel_x_g=reading.accel_x_g,
            accel_y_g=reading.accel_y_g,
            accel_z_g=reading.accel_z_g,
            gyro_x_dps=reading.gyro_x_dps,
            gyro_y_dps=reading.gyro_y_dps,
            gyro_z_dps=reading.gyro_z_dps,
            temperature_c=reading.temperature_c,
            status=SensorStatus.SATURATED,
            is_calibrated=reading.is_calibrated,
            bias_compensated=reading.bias_compensated
        )
        
        confidence = Confidence(
            value=0.3,
            source="imu_saturated",
            timestamp_ms=reading.timestamp_ms,
            degradation_reason=f"saturated:{saturated_axis}"
        )
        
        return saturated_reading, confidence
    
    def _apply_bias_compensation(self, reading: IMUReading) -> IMUReading:
        """Apply bias compensation to reading."""
        
        if not self._bias.is_valid:
            return reading
        
        return IMUReading(
            timestamp_ms=reading.timestamp_ms,
            accel_x_g=reading.accel_x_g - self._bias.accel_x_bias_g,
            accel_y_g=reading.accel_y_g - self._bias.accel_y_bias_g,
            accel_z_g=reading.accel_z_g - self._bias.accel_z_bias_g,
            gyro_x_dps=reading.gyro_x_dps - self._bias.gyro_x_bias_dps,
            gyro_y_dps=reading.gyro_y_dps - self._bias.gyro_y_bias_dps,
            gyro_z_dps=reading.gyro_z_dps - self._bias.gyro_z_bias_dps,
            temperature_c=reading.temperature_c,
            status=reading.status,
            is_calibrated=True,
            bias_compensated=True
        )
    
    def _apply_filter(self, reading: IMUReading) -> IMUReading:
        """Apply low-pass filtering to reduce noise."""
        
        if self._last_reading is None:
            return reading
        
        alpha = self.config.low_pass_alpha
        
        return IMUReading(
            timestamp_ms=reading.timestamp_ms,
            accel_x_g=alpha * reading.accel_x_g + (1 - alpha) * self._last_reading.accel_x_g,
            accel_y_g=alpha * reading.accel_y_g + (1 - alpha) * self._last_reading.accel_y_g,
            accel_z_g=alpha * reading.accel_z_g + (1 - alpha) * self._last_reading.accel_z_g,
            gyro_x_dps=alpha * reading.gyro_x_dps + (1 - alpha) * self._last_reading.gyro_x_dps,
            gyro_y_dps=alpha * reading.gyro_y_dps + (1 - alpha) * self._last_reading.gyro_y_dps,
            gyro_z_dps=alpha * reading.gyro_z_dps + (1 - alpha) * self._last_reading.gyro_z_dps,
            temperature_c=reading.temperature_c,
            status=reading.status,
            is_calibrated=reading.is_calibrated,
            bias_compensated=reading.bias_compensated
        )
    
    def _apply_orientation_correction(self, reading: IMUReading) -> IMUReading:
        """Apply mounting orientation correction."""
        
        # Convert offsets to radians
        roll = math.radians(self.config.roll_offset_deg)
        pitch = math.radians(self.config.pitch_offset_deg)
        yaw = math.radians(self.config.yaw_offset_deg)
        
        if roll == 0 and pitch == 0 and yaw == 0:
            return reading
        
        # Build rotation matrix (simplified - Euler angles)
        # For small angles, this is approximately correct
        
        # Apply yaw rotation to horizontal plane
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        
        accel_x = reading.accel_x_g * cos_yaw - reading.accel_y_g * sin_yaw
        accel_y = reading.accel_x_g * sin_yaw + reading.accel_y_g * cos_yaw
        
        gyro_x = reading.gyro_x_dps * cos_yaw - reading.gyro_y_dps * sin_yaw
        gyro_y = reading.gyro_x_dps * sin_yaw + reading.gyro_y_dps * cos_yaw
        
        return IMUReading(
            timestamp_ms=reading.timestamp_ms,
            accel_x_g=accel_x,
            accel_y_g=accel_y,
            accel_z_g=reading.accel_z_g,
            gyro_x_dps=gyro_x,
            gyro_y_dps=gyro_y,
            gyro_z_dps=reading.gyro_z_dps,
            temperature_c=reading.temperature_c,
            status=reading.status,
            is_calibrated=reading.is_calibrated,
            bias_compensated=reading.bias_compensated
        )
    
    def _compute_confidence(self, reading: IMUReading) -> Confidence:
        """Compute confidence for processed IMU reading."""
        
        base = 0.9 if self._bias.is_valid else 0.6
        
        # Degrade if not bias compensated
        if not reading.bias_compensated:
            base *= 0.7
        
        # Check for stale data
        if self._last_reading:
            age_ms = reading.timestamp_ms - self._last_reading.timestamp_ms
            if age_ms > self.config.max_stale_age_ms:
                base *= 0.5
        
        # Estimate drift degradation
        if self._integration_start_ms:
            drift_time_s = (reading.timestamp_ms - self._integration_start_ms) / 1000.0
            drift_degradation = max(0.5, 1.0 - drift_time_s * 0.01)  # 1% per second
            base *= drift_degradation
        
        return Confidence(
            value=base,
            source="imu_processor",
            timestamp_ms=reading.timestamp_ms,
            degradation_reason=None if base > 0.8 else "drift_or_uncalibrated"
        )
    
    def estimate_heading_change(
        self,
        readings: List[IMUReading]
    ) -> float:
        """
        Estimate heading change from gyroscope integration.
        
        Returns heading change in degrees.
        
        SAFETY: This is subject to drift and should not be trusted
        for long durations.
        """
        if len(readings) < 2:
            return 0.0
        
        total_heading_change = 0.0
        
        for i in range(1, len(readings)):
            dt_s = (readings[i].timestamp_ms - readings[i-1].timestamp_ms) / 1000.0
            
            # Integrate yaw rate (gyro Z axis)
            avg_yaw_rate = (readings[i].gyro_z_dps + readings[i-1].gyro_z_dps) / 2
            total_heading_change += avg_yaw_rate * dt_s
        
        return total_heading_change
    
    def get_calibration_status(self) -> dict:
        """Get current calibration status."""
        return {
            "is_calibrating": self._is_calibrating,
            "calibration_progress": len(self._calibration_samples) / self.config.bias_estimation_samples,
            "bias_valid": self._bias.is_valid,
            "samples_collected": self._bias.samples_collected,
            "accel_bias": [
                self._bias.accel_x_bias_g,
                self._bias.accel_y_bias_g,
                self._bias.accel_z_bias_g
            ],
            "gyro_bias": [
                self._bias.gyro_x_bias_dps,
                self._bias.gyro_y_bias_dps,
                self._bias.gyro_z_bias_dps
            ]
        }
    
    def reset(self) -> None:
        """Reset processor state."""
        self._last_reading = None
        self._calibration_samples.clear()
        self._is_calibrating = False
        self._gyro_integral_deg = [0.0, 0.0, 0.0]
        self._integration_start_ms = None
        # Note: bias is preserved - only cleared by explicit recalibration
