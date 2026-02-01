"""
Entry Speed Detector
Safety-Critical Adaptive AI Race Coaching System

Detects when entry speed is too high for upcoming corner.

SAFETY: Uses physics-based envelopes as reference.
Warning must come with sufficient time for driver to react.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List

from ..types.envelopes import CornerSpeedEnvelope
from ..types.geometry import TrackSegment, CornerPhase


class EntrySpeedFlag(Enum):
    """Entry speed warning levels."""
    
    NONE = auto()          # Speed is OK
    APPROACHING_LIMIT = auto()  # Getting close
    TOO_FAST = auto()      # Entry speed exceeds envelope
    CRITICAL = auto()      # Significantly over, intervention needed


@dataclass
class EntrySpeedConfig:
    """Configuration for entry speed detection."""
    
    # Threshold percentages above envelope
    approaching_threshold_pct: float = 0.05   # 5% above envelope
    too_fast_threshold_pct: float = 0.10      # 10% above envelope
    critical_threshold_pct: float = 0.20      # 20% above envelope
    
    # Minimum warning distance
    min_warning_distance_m: float = 50.0
    preferred_warning_distance_m: float = 100.0
    
    # Speed trend requirements
    require_speed_trend: bool = True  # Must be maintaining/increasing
    trend_window_ms: int = 500
    
    # Confidence requirements
    min_confidence_for_warning: float = 0.85


@dataclass
class EntrySpeedResult:
    """Result from entry speed detection."""
    
    flag: EntrySpeedFlag
    current_speed_kmh: float
    envelope_speed_kmh: float
    excess_pct: float
    distance_to_corner_m: float
    confidence: float
    should_warn: bool = False
    
    @property
    def message(self) -> str:
        """Human-readable message for the flag."""
        if self.flag == EntrySpeedFlag.NONE:
            return ""
        elif self.flag == EntrySpeedFlag.APPROACHING_LIMIT:
            return "Entry speed"
        elif self.flag == EntrySpeedFlag.TOO_FAST:
            return "Slow in"
        elif self.flag == EntrySpeedFlag.CRITICAL:
            return "Entry speed"
        return ""


class EntrySpeedDetector:
    """
    Detects excessive entry speed for upcoming corners.
    
    Compares current speed and trajectory with physics-based
    envelope for the upcoming corner. Flags when driver is
    approaching too fast to make the corner safely.
    
    SAFETY REQUIREMENTS:
    - Warning must come early enough for driver to react
    - Must not false-positive on normal driving
    - High confidence required before warning
    """
    
    def __init__(self, config: Optional[EntrySpeedConfig] = None):
        self.config = config or EntrySpeedConfig()
        
        # Speed history for trend detection
        self._speed_history: List[tuple] = []  # (timestamp_ms, speed_kmh)
        self._max_history_size = 50
        
        # False positive suppression
        self._last_warning_timestamp_ms: int = 0
        self._warning_cooldown_ms: int = 2000
    
    def check_entry_speed(
        self,
        current_speed_kmh: float,
        envelope: CornerSpeedEnvelope,
        distance_to_corner_m: float,
        timestamp_ms: int,
        confidence: float
    ) -> EntrySpeedResult:
        """
        Check if current speed is safe for upcoming corner.
        
        Args:
            current_speed_kmh: Current vehicle speed
            envelope: Physics envelope for the upcoming corner
            distance_to_corner_m: Distance to corner entry
            timestamp_ms: Current timestamp
            confidence: Sensor confidence
            
        Returns:
            EntrySpeedResult with flag and details
        """
        # Record speed for trend analysis
        self._record_speed(timestamp_ms, current_speed_kmh)
        
        # Get envelope speed limit
        envelope_speed = envelope.max_speed_kmh
        
        # Compute excess percentage
        if envelope_speed > 0:
            excess_pct = (current_speed_kmh - envelope_speed) / envelope_speed
        else:
            excess_pct = 0.0
        
        # Determine flag level
        flag = self._determine_flag(excess_pct)
        
        # Determine if we should warn
        should_warn = self._should_warn(
            flag=flag,
            distance_to_corner_m=distance_to_corner_m,
            timestamp_ms=timestamp_ms,
            confidence=confidence
        )
        
        return EntrySpeedResult(
            flag=flag,
            current_speed_kmh=current_speed_kmh,
            envelope_speed_kmh=envelope_speed,
            excess_pct=excess_pct,
            distance_to_corner_m=distance_to_corner_m,
            confidence=confidence,
            should_warn=should_warn
        )
    
    def _determine_flag(self, excess_pct: float) -> EntrySpeedFlag:
        """Determine flag level from excess percentage."""
        
        if excess_pct >= self.config.critical_threshold_pct:
            return EntrySpeedFlag.CRITICAL
        elif excess_pct >= self.config.too_fast_threshold_pct:
            return EntrySpeedFlag.TOO_FAST
        elif excess_pct >= self.config.approaching_threshold_pct:
            return EntrySpeedFlag.APPROACHING_LIMIT
        else:
            return EntrySpeedFlag.NONE
    
    def _should_warn(
        self,
        flag: EntrySpeedFlag,
        distance_to_corner_m: float,
        timestamp_ms: int,
        confidence: float
    ) -> bool:
        """Determine if we should issue a warning."""
        
        # No warning for NONE flag
        if flag == EntrySpeedFlag.NONE:
            return False
        
        # Check confidence
        if confidence < self.config.min_confidence_for_warning:
            return False
        
        # Check distance (too close = too late to help)
        if distance_to_corner_m < self.config.min_warning_distance_m:
            return False
        
        # Check cooldown (prevent rapid-fire warnings)
        if timestamp_ms - self._last_warning_timestamp_ms < self._warning_cooldown_ms:
            # Allow critical to override cooldown
            if flag != EntrySpeedFlag.CRITICAL:
                return False
        
        # Check speed trend (if required)
        if self.config.require_speed_trend:
            trend = self._get_speed_trend()
            # Only warn if speed is stable or increasing
            # (driver already slowing = no need to warn)
            if trend < -5.0:  # Decelerating more than 5 km/h in window
                return False
        
        # All checks passed - record and warn
        if flag != EntrySpeedFlag.NONE:
            self._last_warning_timestamp_ms = timestamp_ms
        
        return True
    
    def _record_speed(self, timestamp_ms: int, speed_kmh: float) -> None:
        """Record speed for trend analysis."""
        self._speed_history.append((timestamp_ms, speed_kmh))
        
        # Trim old entries
        if len(self._speed_history) > self._max_history_size:
            self._speed_history.pop(0)
    
    def _get_speed_trend(self) -> float:
        """
        Get speed trend (km/h change over trend window).
        
        Positive = accelerating
        Negative = decelerating
        """
        if len(self._speed_history) < 2:
            return 0.0
        
        latest_time, latest_speed = self._speed_history[-1]
        oldest_valid_time = latest_time - self.config.trend_window_ms
        
        # Find oldest entry within window
        for timestamp, speed in self._speed_history:
            if timestamp >= oldest_valid_time:
                return latest_speed - speed
        
        # No valid entries in window
        return 0.0
    
    def reset(self) -> None:
        """Reset detector state."""
        self._speed_history.clear()
        self._last_warning_timestamp_ms = 0
