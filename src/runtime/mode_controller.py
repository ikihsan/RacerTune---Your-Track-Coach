"""
Mode Controller
Safety-Critical Adaptive AI Race Coaching System

Controls operating modes and mode transitions.

OPERATING MODES:
- SILENT: Record only, no voice output (initial state)
- LEARNING: Record and analyze, limited voice
- COACHING: Full coaching, voice enabled
- DEGRADED: Reduced functionality, critical voice only
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List, Set
from datetime import datetime


class OperatingMode(Enum):
    """System operating modes."""
    
    SILENT = auto()     # Record only, no voice
    LEARNING = auto()   # Recording + learning, limited voice
    COACHING = auto()   # Full coaching mode
    DEGRADED = auto()   # Safety-only mode
    OFF = auto()        # System disabled


@dataclass
class ModeRequirements:
    """Requirements for each operating mode."""
    
    # Minimum clean laps for mode
    min_clean_laps: int
    
    # Minimum track coverage percentage
    min_track_coverage: float
    
    # Minimum confidence level
    min_confidence: float
    
    # Maximum allowed sensor issues
    max_sensor_issues: int
    
    # Voice enabled
    voice_enabled: bool
    
    # Learning enabled
    learning_enabled: bool


class ModeController:
    """
    Controls operating mode transitions.
    
    The system starts in SILENT mode and must earn the right
    to provide coaching through clean laps and good data.
    
    MODE PROGRESSION:
    SILENT -> LEARNING -> COACHING
    Any mode can degrade to DEGRADED on errors
    DEGRADED can recover to previous mode when issues resolve
    """
    
    # Mode requirements
    MODE_REQUIREMENTS = {
        OperatingMode.SILENT: ModeRequirements(
            min_clean_laps=0,
            min_track_coverage=0.0,
            min_confidence=0.0,
            max_sensor_issues=999,
            voice_enabled=False,
            learning_enabled=True
        ),
        OperatingMode.LEARNING: ModeRequirements(
            min_clean_laps=1,
            min_track_coverage=0.90,
            min_confidence=0.70,
            max_sensor_issues=5,
            voice_enabled=True,  # Limited
            learning_enabled=True
        ),
        OperatingMode.COACHING: ModeRequirements(
            min_clean_laps=3,
            min_track_coverage=0.95,
            min_confidence=0.85,
            max_sensor_issues=2,
            voice_enabled=True,
            learning_enabled=True
        ),
        OperatingMode.DEGRADED: ModeRequirements(
            min_clean_laps=0,
            min_track_coverage=0.0,
            min_confidence=0.0,
            max_sensor_issues=999,
            voice_enabled=True,  # Critical only
            learning_enabled=False
        ),
    }
    
    def __init__(self):
        self._current_mode = OperatingMode.SILENT
        self._previous_mode: Optional[OperatingMode] = None
        
        # State tracking
        self._clean_lap_count = 0
        self._track_coverage = 0.0
        self._current_confidence = 0.0
        self._sensor_issue_count = 0
        
        # Mode history
        self._mode_history: List[tuple] = []  # (timestamp, mode, reason)
    
    @property
    def current_mode(self) -> OperatingMode:
        """Get current operating mode."""
        return self._current_mode
    
    @property
    def voice_enabled(self) -> bool:
        """Check if voice output is enabled in current mode."""
        return self.MODE_REQUIREMENTS[self._current_mode].voice_enabled
    
    @property
    def learning_enabled(self) -> bool:
        """Check if learning is enabled in current mode."""
        return self.MODE_REQUIREMENTS[self._current_mode].learning_enabled
    
    def update_state(
        self,
        clean_laps: int,
        track_coverage: float,
        confidence: float,
        sensor_issues: int
    ) -> Optional[OperatingMode]:
        """
        Update state and check for mode transitions.
        
        Args:
            clean_laps: Number of clean laps completed
            track_coverage: Track coverage percentage (0-1)
            confidence: Current system confidence (0-1)
            sensor_issues: Count of current sensor issues
            
        Returns:
            New mode if transition occurred, None otherwise
        """
        self._clean_lap_count = clean_laps
        self._track_coverage = track_coverage
        self._current_confidence = confidence
        self._sensor_issue_count = sensor_issues
        
        # Check for degradation
        if self._should_degrade():
            return self._transition_to(OperatingMode.DEGRADED, "quality_degraded")
        
        # Check for recovery from degraded
        if self._current_mode == OperatingMode.DEGRADED:
            if self._can_recover():
                return self._transition_to(
                    self._previous_mode or OperatingMode.LEARNING,
                    "recovered"
                )
        
        # Check for upgrade
        new_mode = self._check_upgrade()
        if new_mode and new_mode != self._current_mode:
            return self._transition_to(new_mode, "requirements_met")
        
        return None
    
    def _should_degrade(self) -> bool:
        """Check if system should degrade."""
        
        if self._current_mode == OperatingMode.DEGRADED:
            return False
        
        if self._current_mode == OperatingMode.OFF:
            return False
        
        # Check confidence
        if self._current_confidence < 0.5:
            return True
        
        # Check sensor issues
        if self._sensor_issue_count > 10:
            return True
        
        return False
    
    def _can_recover(self) -> bool:
        """Check if system can recover from degraded mode."""
        
        if self._previous_mode is None:
            return self._current_confidence >= 0.7
        
        requirements = self.MODE_REQUIREMENTS[self._previous_mode]
        
        return (
            self._current_confidence >= requirements.min_confidence and
            self._sensor_issue_count <= requirements.max_sensor_issues
        )
    
    def _check_upgrade(self) -> Optional[OperatingMode]:
        """Check if system can upgrade to higher mode."""
        
        if self._current_mode == OperatingMode.OFF:
            return None
        
        if self._current_mode == OperatingMode.DEGRADED:
            return None
        
        # Check each higher mode
        modes_to_check = [OperatingMode.COACHING, OperatingMode.LEARNING]
        
        for mode in modes_to_check:
            if mode.value <= self._current_mode.value:
                continue
            
            if self._meets_requirements(mode):
                return mode
        
        return None
    
    def _meets_requirements(self, mode: OperatingMode) -> bool:
        """Check if current state meets mode requirements."""
        
        req = self.MODE_REQUIREMENTS[mode]
        
        return (
            self._clean_lap_count >= req.min_clean_laps and
            self._track_coverage >= req.min_track_coverage and
            self._current_confidence >= req.min_confidence and
            self._sensor_issue_count <= req.max_sensor_issues
        )
    
    def _transition_to(self, mode: OperatingMode, reason: str) -> OperatingMode:
        """Execute mode transition."""
        
        if mode != OperatingMode.DEGRADED:
            self._previous_mode = self._current_mode
        
        self._current_mode = mode
        self._mode_history.append((datetime.now(), mode, reason))
        
        return mode
    
    def force_mode(self, mode: OperatingMode, reason: str = "manual") -> None:
        """Force a specific mode (for testing/override)."""
        self._transition_to(mode, reason)
    
    def get_mode_history(self) -> List[tuple]:
        """Get mode transition history."""
        return list(self._mode_history)
    
    def get_status(self) -> dict:
        """Get current status."""
        return {
            "mode": self._current_mode.name,
            "voice_enabled": self.voice_enabled,
            "learning_enabled": self.learning_enabled,
            "clean_laps": self._clean_lap_count,
            "track_coverage": self._track_coverage,
            "confidence": self._current_confidence,
            "sensor_issues": self._sensor_issue_count
        }
    
    def reset(self) -> None:
        """Reset to initial state."""
        self._current_mode = OperatingMode.SILENT
        self._previous_mode = None
        self._clean_lap_count = 0
        self._track_coverage = 0.0
        self._current_confidence = 0.0
        self._sensor_issue_count = 0
        self._mode_history.clear()
