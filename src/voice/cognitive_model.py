"""
Cognitive Load Model
Safety-Critical Adaptive AI Race Coaching System

Models driver cognitive load to determine when voice output is appropriate.

SAFETY INVARIANT S6: Mid-corner speech is forbidden unless instability imminent.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List

from ..types.geometry import CornerPhase


class CognitiveLoadLevel(Enum):
    """Driver cognitive load levels."""
    
    LOW = auto()      # Straight, pit lane - speech OK
    MEDIUM = auto()   # Approach, exit - limited speech
    HIGH = auto()     # Entry - restricted speech  
    CRITICAL = auto() # Apex - NO speech except safety


@dataclass
class CognitiveLoadConfig:
    """Configuration for cognitive load model."""
    
    # Minimum time between messages
    min_message_interval_s: float = 3.0
    
    # Maximum messages per lap
    max_messages_per_lap: int = 10
    
    # Phase-specific limits
    max_messages_per_corner: int = 2
    max_approach_messages: int = 1
    max_exit_messages: int = 1
    
    # Speed thresholds
    high_speed_threshold_kmh: float = 150.0
    very_high_speed_threshold_kmh: float = 200.0
    
    # G-force thresholds
    high_g_threshold: float = 1.0
    very_high_g_threshold: float = 1.5


@dataclass
class CognitiveState:
    """Current cognitive load state."""
    
    level: CognitiveLoadLevel
    phase: CornerPhase
    speed_kmh: float
    lateral_g: float
    time_since_last_message_s: float
    messages_this_lap: int
    messages_this_corner: int
    
    @property
    def allows_speech(self) -> bool:
        """Check if speech is currently allowed."""
        
        # SAFETY: Apex phase blocks all non-critical speech
        if self.phase == CornerPhase.APEX:
            return False
        
        # Check cognitive load level
        if self.level == CognitiveLoadLevel.CRITICAL:
            return False
        
        return True
    
    @property
    def allows_non_critical_speech(self) -> bool:
        """Check if non-critical speech is allowed."""
        
        if not self.allows_speech:
            return False
        
        if self.level == CognitiveLoadLevel.HIGH:
            return False
        
        return True


class CognitiveLoadModel:
    """
    Models driver cognitive load for voice arbitration.
    
    The model considers:
    - Corner phase (entry/apex/exit)
    - Current speed
    - G-forces
    - Time since last message
    - Message count limits
    
    SAFETY:
    - Silence is a feature, not a failure
    - Driver attention is a limited resource
    - High workload = no voice output
    """
    
    def __init__(self, config: Optional[CognitiveLoadConfig] = None):
        self.config = config or CognitiveLoadConfig()
        
        # State tracking
        self._last_message_timestamp_ms: int = 0
        self._messages_this_lap: int = 0
        self._messages_this_corner: int = 0
        self._current_corner_id: int = -1
    
    def compute_load(
        self,
        phase: CornerPhase,
        speed_kmh: float,
        lateral_g: float,
        current_timestamp_ms: int,
        corner_id: int = 0
    ) -> CognitiveState:
        """
        Compute current cognitive load state.
        
        Args:
            phase: Current corner phase
            speed_kmh: Current speed
            lateral_g: Current lateral acceleration
            current_timestamp_ms: Current timestamp
            corner_id: Current corner ID (for message counting)
            
        Returns:
            CognitiveState with load assessment
        """
        # Reset corner message count if new corner
        if corner_id != self._current_corner_id:
            self._messages_this_corner = 0
            self._current_corner_id = corner_id
        
        # Compute time since last message
        time_since_last = (current_timestamp_ms - self._last_message_timestamp_ms) / 1000.0
        
        # Determine cognitive load level
        level = self._compute_load_level(phase, speed_kmh, lateral_g)
        
        return CognitiveState(
            level=level,
            phase=phase,
            speed_kmh=speed_kmh,
            lateral_g=lateral_g,
            time_since_last_message_s=time_since_last,
            messages_this_lap=self._messages_this_lap,
            messages_this_corner=self._messages_this_corner
        )
    
    def _compute_load_level(
        self,
        phase: CornerPhase,
        speed_kmh: float,
        lateral_g: float
    ) -> CognitiveLoadLevel:
        """Compute cognitive load level from driving state."""
        
        # APEX is always CRITICAL
        if phase == CornerPhase.APEX:
            return CognitiveLoadLevel.CRITICAL
        
        # High G-forces indicate high workload
        if abs(lateral_g) >= self.config.very_high_g_threshold:
            return CognitiveLoadLevel.CRITICAL
        
        if abs(lateral_g) >= self.config.high_g_threshold:
            return CognitiveLoadLevel.HIGH
        
        # Entry phase is high workload
        if phase == CornerPhase.ENTRY:
            return CognitiveLoadLevel.HIGH
        
        # High speed increases workload
        if speed_kmh >= self.config.very_high_speed_threshold_kmh:
            return CognitiveLoadLevel.HIGH
        
        if speed_kmh >= self.config.high_speed_threshold_kmh:
            return CognitiveLoadLevel.MEDIUM
        
        # Exit phase is medium workload
        if phase == CornerPhase.EXIT:
            return CognitiveLoadLevel.MEDIUM
        
        # Approach phase is medium workload
        if phase == CornerPhase.APPROACH:
            return CognitiveLoadLevel.MEDIUM
        
        # Straight is low workload
        return CognitiveLoadLevel.LOW
    
    def can_speak(self, state: CognitiveState, is_critical: bool = False) -> tuple:
        """
        Determine if speech is allowed in current state.
        
        Args:
            state: Current cognitive state
            is_critical: Whether this is a critical safety message
            
        Returns:
            Tuple of (can_speak, reason)
        """
        # Critical messages can override most restrictions
        if is_critical:
            # But not during actual instability (driver needs full focus)
            if state.level == CognitiveLoadLevel.CRITICAL and state.lateral_g > 1.5:
                return False, "extreme_workload"
            return True, "critical_override"
        
        # Check phase restriction
        if state.phase == CornerPhase.APEX:
            return False, "apex_phase"
        
        # Check load level
        if state.level == CognitiveLoadLevel.CRITICAL:
            return False, "critical_load"
        
        if state.level == CognitiveLoadLevel.HIGH:
            return False, "high_load"
        
        # Check message interval
        if state.time_since_last_message_s < self.config.min_message_interval_s:
            return False, "too_soon"
        
        # Check lap message limit
        if state.messages_this_lap >= self.config.max_messages_per_lap:
            return False, "lap_limit"
        
        # Check corner message limit
        if state.messages_this_corner >= self.config.max_messages_per_corner:
            return False, "corner_limit"
        
        # Phase-specific limits
        if state.phase == CornerPhase.APPROACH:
            if state.messages_this_corner >= self.config.max_approach_messages:
                return False, "approach_limit"
        
        if state.phase == CornerPhase.EXIT:
            if state.messages_this_corner >= self.config.max_exit_messages:
                return False, "exit_limit"
        
        return True, "allowed"
    
    def record_message(self, timestamp_ms: int) -> None:
        """Record that a message was spoken."""
        self._last_message_timestamp_ms = timestamp_ms
        self._messages_this_lap += 1
        self._messages_this_corner += 1
    
    def new_lap(self) -> None:
        """Reset lap-level counters for new lap."""
        self._messages_this_lap = 0
        self._messages_this_corner = 0
        self._current_corner_id = -1
    
    def reset(self) -> None:
        """Reset all state."""
        self._last_message_timestamp_ms = 0
        self._messages_this_lap = 0
        self._messages_this_corner = 0
        self._current_corner_id = -1
