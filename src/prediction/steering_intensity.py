"""
Steering Intensity Detector
Safety-Critical Adaptive AI Race Coaching System

Detects aggressive or unsafe steering inputs.

SAFETY: Monitors steering intensity relative to available grip.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List
import math


class SteeringFlag(Enum):
    """Steering warning flags."""
    
    NONE = auto()            # Normal steering
    AGGRESSIVE = auto()      # Steering rate high
    CORRECTION = auto()      # Counter-steering detected
    INSTABILITY = auto()     # Vehicle appears unstable


@dataclass
class SteeringConfig:
    """Configuration for steering detection."""
    
    # Steering rate thresholds (deg/s)
    aggressive_rate_threshold: float = 150.0
    correction_rate_threshold: float = 200.0
    
    # Steering angle thresholds (deg)
    high_angle_threshold: float = 45.0
    
    # Yaw rate correlation
    max_yaw_steering_lag_ms: int = 200
    yaw_correlation_threshold: float = 0.7
    
    # Instability detection
    counter_steer_count_for_instability: int = 3
    counter_steer_window_ms: int = 1000
    
    # Confidence
    min_confidence: float = 0.80


@dataclass
class SteeringResult:
    """Result from steering analysis."""
    
    flag: SteeringFlag
    steering_rate_deg_s: float
    steering_angle_deg: float
    is_counter_steering: bool
    grip_usage_pct: float
    confidence: float
    should_warn: bool = False


class SteeringIntensityDetector:
    """
    Detects aggressive or unsafe steering patterns.
    
    Monitors:
    - Steering rate (abrupt inputs)
    - Counter-steering (corrections)
    - Steering vs yaw correlation (vehicle response)
    
    SAFETY FOCUS:
    - Detect vehicle instability early
    - Warn before spin, not during
    - Don't distract stable driver
    """
    
    def __init__(self, config: Optional[SteeringConfig] = None):
        self.config = config or SteeringConfig()
        
        # History for pattern detection
        self._steering_history: List[tuple] = []  # (timestamp_ms, angle_deg, rate_deg_s)
        self._yaw_history: List[tuple] = []  # (timestamp_ms, yaw_rate_deg_s)
        self._counter_steer_times: List[int] = []  # timestamps of counter-steers
        
        self._max_history_size = 100
        self._previous_angle: Optional[float] = None
        self._previous_timestamp: Optional[int] = None
    
    def check_steering(
        self,
        steering_angle_deg: float,
        yaw_rate_deg_s: float,
        lateral_g: float,
        timestamp_ms: int,
        confidence: float
    ) -> SteeringResult:
        """
        Analyze steering inputs for safety.
        
        Args:
            steering_angle_deg: Current steering wheel angle
            yaw_rate_deg_s: Vehicle yaw rate
            lateral_g: Lateral acceleration
            timestamp_ms: Current timestamp
            confidence: Sensor confidence
            
        Returns:
            SteeringResult with flag and analysis
        """
        # Compute steering rate
        steering_rate = self._compute_steering_rate(steering_angle_deg, timestamp_ms)
        
        # Record history
        self._record_steering(timestamp_ms, steering_angle_deg, steering_rate)
        self._record_yaw(timestamp_ms, yaw_rate_deg_s)
        
        # Detect counter-steering
        is_counter_steering = self._detect_counter_steer(
            steering_angle_deg, yaw_rate_deg_s, timestamp_ms
        )
        
        # Estimate grip usage
        grip_usage = self._estimate_grip_usage(lateral_g, steering_angle_deg)
        
        # Determine flag
        flag = self._determine_flag(
            steering_rate=steering_rate,
            steering_angle=steering_angle_deg,
            is_counter_steering=is_counter_steering,
            timestamp_ms=timestamp_ms
        )
        
        # Determine if we should warn
        should_warn = flag in [SteeringFlag.INSTABILITY] and confidence >= self.config.min_confidence
        
        return SteeringResult(
            flag=flag,
            steering_rate_deg_s=steering_rate,
            steering_angle_deg=steering_angle_deg,
            is_counter_steering=is_counter_steering,
            grip_usage_pct=grip_usage,
            confidence=confidence,
            should_warn=should_warn
        )
    
    def _compute_steering_rate(self, current_angle: float, timestamp_ms: int) -> float:
        """Compute steering rate from consecutive readings."""
        
        if self._previous_angle is None or self._previous_timestamp is None:
            self._previous_angle = current_angle
            self._previous_timestamp = timestamp_ms
            return 0.0
        
        dt_s = (timestamp_ms - self._previous_timestamp) / 1000.0
        
        if dt_s <= 0:
            return 0.0
        
        rate = (current_angle - self._previous_angle) / dt_s
        
        self._previous_angle = current_angle
        self._previous_timestamp = timestamp_ms
        
        return rate
    
    def _detect_counter_steer(
        self,
        steering_angle: float,
        yaw_rate: float,
        timestamp_ms: int
    ) -> bool:
        """
        Detect counter-steering (steering opposite to yaw).
        
        Counter-steering indicates the driver is correcting
        for oversteer or understeer.
        """
        # Counter-steer: steering and yaw have opposite signs
        # (steering left but car rotating right, or vice versa)
        
        if abs(steering_angle) < 5.0 or abs(yaw_rate) < 5.0:
            return False
        
        # Check sign mismatch
        steering_sign = 1 if steering_angle > 0 else -1
        yaw_sign = 1 if yaw_rate > 0 else -1
        
        is_counter = steering_sign != yaw_sign
        
        if is_counter:
            self._counter_steer_times.append(timestamp_ms)
            # Clean old entries
            cutoff = timestamp_ms - self.config.counter_steer_window_ms
            self._counter_steer_times = [t for t in self._counter_steer_times if t > cutoff]
        
        return is_counter
    
    def _estimate_grip_usage(self, lateral_g: float, steering_angle: float) -> float:
        """Estimate percentage of available grip being used."""
        
        # Simple model: grip usage proportional to lateral G
        # Assume max grip around 1.2G for street car, 1.5G for track car
        max_grip_g = 1.3
        
        grip_usage = min(abs(lateral_g) / max_grip_g, 1.0)
        
        return grip_usage * 100.0
    
    def _determine_flag(
        self,
        steering_rate: float,
        steering_angle: float,
        is_counter_steering: bool,
        timestamp_ms: int
    ) -> SteeringFlag:
        """Determine steering flag based on analysis."""
        
        # Check for instability (multiple counter-steers)
        if len(self._counter_steer_times) >= self.config.counter_steer_count_for_instability:
            return SteeringFlag.INSTABILITY
        
        # Check for correction
        if is_counter_steering and abs(steering_rate) > self.config.correction_rate_threshold:
            return SteeringFlag.CORRECTION
        
        # Check for aggressive steering
        if abs(steering_rate) > self.config.aggressive_rate_threshold:
            return SteeringFlag.AGGRESSIVE
        
        return SteeringFlag.NONE
    
    def _record_steering(self, timestamp_ms: int, angle: float, rate: float) -> None:
        """Record steering history."""
        self._steering_history.append((timestamp_ms, angle, rate))
        if len(self._steering_history) > self._max_history_size:
            self._steering_history.pop(0)
    
    def _record_yaw(self, timestamp_ms: int, yaw_rate: float) -> None:
        """Record yaw history."""
        self._yaw_history.append((timestamp_ms, yaw_rate))
        if len(self._yaw_history) > self._max_history_size:
            self._yaw_history.pop(0)
    
    def reset(self) -> None:
        """Reset detector state."""
        self._steering_history.clear()
        self._yaw_history.clear()
        self._counter_steer_times.clear()
        self._previous_angle = None
        self._previous_timestamp = None
