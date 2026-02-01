"""
Braking Point Detector
Safety-Critical Adaptive AI Race Coaching System

Detects late braking and provides braking point guidance.

SAFETY: Uses physics-based envelope as minimum safe distance.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List

from ..types.envelopes import BrakingEnvelope


class BrakingFlag(Enum):
    """Braking warning flags."""
    
    NONE = auto()           # No issue
    BRAKE_NOW = auto()      # Should brake now
    LATE_BRAKING = auto()   # Past optimal point
    TOO_LATE = auto()       # May not be able to slow enough


@dataclass
class BrakingConfig:
    """Configuration for braking detection."""
    
    # Threshold multipliers on minimum brake distance
    optimal_multiplier: float = 1.3    # 30% earlier than minimum
    warning_multiplier: float = 1.1    # 10% earlier than minimum
    critical_multiplier: float = 0.95  # Past minimum
    
    # Speed thresholds for braking detection
    min_speed_for_braking_kmh: float = 60.0
    
    # Brake detection
    brake_threshold_g: float = 0.3  # G to consider "braking"
    
    # Confidence
    min_confidence: float = 0.85


@dataclass
class BrakingResult:
    """Result from braking point detection."""
    
    flag: BrakingFlag
    distance_to_brake_point_m: float
    minimum_brake_distance_m: float
    current_speed_kmh: float
    is_braking: bool
    confidence: float
    should_warn: bool = False


class BrakingPointDetector:
    """
    Detects braking point timing relative to envelope.
    
    Monitors vehicle position relative to the physics-based
    minimum brake point for upcoming corners.
    
    WARNING TIMING:
    - Before optimal: No warning
    - At optimal: Consider "Brake" call
    - Between optimal and minimum: "Brake now"
    - Past minimum: "Late braking" (may be too late)
    """
    
    def __init__(self, config: Optional[BrakingConfig] = None):
        self.config = config or BrakingConfig()
        
        # State tracking
        self._last_warning_segment: int = -1
        self._braking_started_for_segment: bool = False
    
    def check_braking_point(
        self,
        distance_to_corner_m: float,
        current_speed_kmh: float,
        envelope: BrakingEnvelope,
        longitudinal_g: float,
        segment_id: int,
        confidence: float
    ) -> BrakingResult:
        """
        Check if driver is approaching brake point correctly.
        
        Args:
            distance_to_corner_m: Distance to corner entry point
            current_speed_kmh: Current vehicle speed
            envelope: Physics braking envelope
            longitudinal_g: Current longitudinal acceleration (negative = braking)
            segment_id: Current segment ID
            confidence: Sensor confidence
            
        Returns:
            BrakingResult with flag and details
        """
        # Reset state for new segment
        if segment_id != self._last_warning_segment:
            self._braking_started_for_segment = False
        
        # Check if driver is already braking
        is_braking = longitudinal_g < -self.config.brake_threshold_g
        
        if is_braking:
            self._braking_started_for_segment = True
        
        # Get minimum brake distance from envelope
        min_brake_distance = envelope.minimum_brake_distance_m
        
        # Compute threshold distances
        optimal_distance = min_brake_distance * self.config.optimal_multiplier
        warning_distance = min_brake_distance * self.config.warning_multiplier
        critical_distance = min_brake_distance * self.config.critical_multiplier
        
        # Determine flag
        flag = self._determine_flag(
            distance_to_corner_m=distance_to_corner_m,
            optimal_distance=optimal_distance,
            warning_distance=warning_distance,
            critical_distance=critical_distance,
            is_braking=is_braking,
            current_speed_kmh=current_speed_kmh
        )
        
        # Determine if we should warn
        should_warn = self._should_warn(
            flag=flag,
            is_braking=is_braking,
            segment_id=segment_id,
            confidence=confidence
        )
        
        return BrakingResult(
            flag=flag,
            distance_to_brake_point_m=distance_to_corner_m - min_brake_distance,
            minimum_brake_distance_m=min_brake_distance,
            current_speed_kmh=current_speed_kmh,
            is_braking=is_braking,
            confidence=confidence,
            should_warn=should_warn
        )
    
    def _determine_flag(
        self,
        distance_to_corner_m: float,
        optimal_distance: float,
        warning_distance: float,
        critical_distance: float,
        is_braking: bool,
        current_speed_kmh: float
    ) -> BrakingFlag:
        """Determine braking flag based on position and state."""
        
        # Not fast enough to need braking warning
        if current_speed_kmh < self.config.min_speed_for_braking_kmh:
            return BrakingFlag.NONE
        
        # Already braking - no need for brake call
        if is_braking:
            # But check if braking started too late
            if distance_to_corner_m < critical_distance and not self._braking_started_for_segment:
                return BrakingFlag.TOO_LATE
            return BrakingFlag.NONE
        
        # Not braking yet - check distance
        if distance_to_corner_m > optimal_distance:
            return BrakingFlag.NONE
        elif distance_to_corner_m > warning_distance:
            return BrakingFlag.BRAKE_NOW
        elif distance_to_corner_m > critical_distance:
            return BrakingFlag.LATE_BRAKING
        else:
            return BrakingFlag.TOO_LATE
    
    def _should_warn(
        self,
        flag: BrakingFlag,
        is_braking: bool,
        segment_id: int,
        confidence: float
    ) -> bool:
        """Determine if we should issue a warning."""
        
        if flag == BrakingFlag.NONE:
            return False
        
        if confidence < self.config.min_confidence:
            return False
        
        # Already braking - don't nag
        if is_braking:
            return False
        
        # Already warned for this segment
        if segment_id == self._last_warning_segment:
            # Allow TOO_LATE to override
            if flag != BrakingFlag.TOO_LATE:
                return False
        
        # Issue warning
        self._last_warning_segment = segment_id
        return True
    
    def reset(self) -> None:
        """Reset detector state."""
        self._last_warning_segment = -1
        self._braking_started_for_segment = False
