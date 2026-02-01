"""
Flag Arbiter
Safety-Critical Adaptive AI Race Coaching System

Combines and arbitrates between multiple detection flags.

SAFETY: Implements false-positive suppression and priority handling.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List, Dict

from .entry_speed import EntrySpeedFlag, EntrySpeedResult
from .braking_point import BrakingFlag, BrakingResult
from .steering_intensity import SteeringFlag, SteeringResult
from ..voice.phrase_dictionary import PhraseKey


class CombinedFlag(Enum):
    """Combined/arbitrated flag output."""
    
    NONE = auto()
    
    # Speed-related
    ENTRY_SPEED = auto()
    SLOW_IN = auto()
    
    # Braking-related
    BRAKE = auto()
    BRAKE_EARLIER = auto()
    
    # Steering-related
    SMOOTH_INPUTS = auto()
    
    # Critical
    INSTABILITY = auto()
    LIMIT = auto()


@dataclass
class ArbiterConfig:
    """Configuration for flag arbitration."""
    
    # Minimum confidence for any flag
    min_confidence: float = 0.85
    
    # Maximum flags per corner
    max_flags_per_corner: int = 2
    
    # Cooldown between flags (ms)
    flag_cooldown_ms: int = 2000
    
    # Priority weights (lower = higher priority)
    priority_instability: int = 0
    priority_limit: int = 1
    priority_brake: int = 2
    priority_speed: int = 3
    priority_steering: int = 4
    
    # False positive suppression
    consecutive_detections_required: int = 2
    detection_window_ms: int = 500


@dataclass
class FlagDecision:
    """Decision output from flag arbiter."""
    
    flag: CombinedFlag
    phrase_key: Optional[PhraseKey]
    priority: int
    confidence: float
    source: str
    should_output: bool = False


class FlagArbiter:
    """
    Arbitrates between multiple detection flags.
    
    Combines outputs from entry speed, braking, and steering
    detectors. Suppresses false positives and manages priority.
    
    SAFETY PRINCIPLES:
    - Critical flags (instability) have highest priority
    - False positives are worse than missed warnings
    - Limit message frequency to avoid distraction
    - Silence when uncertain
    """
    
    def __init__(self, config: Optional[ArbiterConfig] = None):
        self.config = config or ArbiterConfig()
        
        # Detection history for false-positive suppression
        self._detection_counts: Dict[CombinedFlag, List[int]] = {}
        
        # Cooldown tracking
        self._last_flag_time_ms: int = 0
        self._flags_this_corner: int = 0
        self._current_corner_id: int = -1
    
    def arbitrate(
        self,
        entry_result: Optional[EntrySpeedResult],
        braking_result: Optional[BrakingResult],
        steering_result: Optional[SteeringResult],
        timestamp_ms: int,
        corner_id: int = 0
    ) -> FlagDecision:
        """
        Arbitrate between detection results.
        
        Args:
            entry_result: Entry speed detection result
            braking_result: Braking point detection result
            steering_result: Steering intensity result
            timestamp_ms: Current timestamp
            corner_id: Current corner ID
            
        Returns:
            FlagDecision with final output decision
        """
        # Reset corner tracking
        if corner_id != self._current_corner_id:
            self._flags_this_corner = 0
            self._current_corner_id = corner_id
        
        # Collect all active flags with priorities
        candidates: List[FlagDecision] = []
        
        # Process steering (highest priority for instability)
        if steering_result:
            decision = self._process_steering(steering_result, timestamp_ms)
            if decision:
                candidates.append(decision)
        
        # Process braking
        if braking_result:
            decision = self._process_braking(braking_result, timestamp_ms)
            if decision:
                candidates.append(decision)
        
        # Process entry speed
        if entry_result:
            decision = self._process_entry_speed(entry_result, timestamp_ms)
            if decision:
                candidates.append(decision)
        
        # No candidates
        if not candidates:
            return FlagDecision(
                flag=CombinedFlag.NONE,
                phrase_key=None,
                priority=999,
                confidence=0.0,
                source="none",
                should_output=False
            )
        
        # Sort by priority
        candidates.sort(key=lambda x: x.priority)
        
        # Get highest priority candidate
        best = candidates[0]
        
        # Check if we should output
        best.should_output = self._should_output(best, timestamp_ms)
        
        if best.should_output:
            self._last_flag_time_ms = timestamp_ms
            self._flags_this_corner += 1
        
        return best
    
    def _process_entry_speed(
        self,
        result: EntrySpeedResult,
        timestamp_ms: int
    ) -> Optional[FlagDecision]:
        """Process entry speed result."""
        
        if result.flag == EntrySpeedFlag.NONE:
            return None
        
        if result.confidence < self.config.min_confidence:
            return None
        
        # Map to combined flag
        if result.flag == EntrySpeedFlag.CRITICAL:
            flag = CombinedFlag.SLOW_IN
            phrase_key = PhraseKey.SLOW_IN
        elif result.flag == EntrySpeedFlag.TOO_FAST:
            flag = CombinedFlag.ENTRY_SPEED
            phrase_key = PhraseKey.ENTRY_SPEED_HIGH
        else:
            flag = CombinedFlag.ENTRY_SPEED
            phrase_key = PhraseKey.ENTRY_SPEED_HIGH
        
        # Check false-positive suppression
        if not self._check_consecutive(flag, timestamp_ms):
            return None
        
        return FlagDecision(
            flag=flag,
            phrase_key=phrase_key,
            priority=self.config.priority_speed,
            confidence=result.confidence,
            source="entry_speed"
        )
    
    def _process_braking(
        self,
        result: BrakingResult,
        timestamp_ms: int
    ) -> Optional[FlagDecision]:
        """Process braking result."""
        
        if result.flag == BrakingFlag.NONE:
            return None
        
        if result.confidence < self.config.min_confidence:
            return None
        
        # Map to combined flag
        if result.flag == BrakingFlag.TOO_LATE:
            flag = CombinedFlag.BRAKE
            phrase_key = PhraseKey.BRAKE_NOW
            priority = self.config.priority_brake
        elif result.flag == BrakingFlag.LATE_BRAKING:
            flag = CombinedFlag.BRAKE
            phrase_key = PhraseKey.BRAKE_NOW
            priority = self.config.priority_brake
        elif result.flag == BrakingFlag.BRAKE_NOW:
            flag = CombinedFlag.BRAKE
            phrase_key = PhraseKey.BRAKE_NOW
            priority = self.config.priority_brake + 1
        else:
            return None
        
        # Check false-positive suppression
        if not self._check_consecutive(flag, timestamp_ms):
            return None
        
        return FlagDecision(
            flag=flag,
            phrase_key=phrase_key,
            priority=priority,
            confidence=result.confidence,
            source="braking"
        )
    
    def _process_steering(
        self,
        result: SteeringResult,
        timestamp_ms: int
    ) -> Optional[FlagDecision]:
        """Process steering result."""
        
        if result.flag == SteeringFlag.NONE:
            return None
        
        if result.confidence < self.config.min_confidence:
            return None
        
        # Map to combined flag
        if result.flag == SteeringFlag.INSTABILITY:
            flag = CombinedFlag.INSTABILITY
            phrase_key = PhraseKey.INSTABILITY
            priority = self.config.priority_instability
        elif result.flag == SteeringFlag.CORRECTION:
            flag = CombinedFlag.SMOOTH_INPUTS
            phrase_key = PhraseKey.SMOOTH_INPUTS
            priority = self.config.priority_steering
        elif result.flag == SteeringFlag.AGGRESSIVE:
            flag = CombinedFlag.SMOOTH_INPUTS
            phrase_key = PhraseKey.SMOOTH_INPUTS
            priority = self.config.priority_steering + 1
        else:
            return None
        
        # Instability bypasses false-positive check
        if flag != CombinedFlag.INSTABILITY:
            if not self._check_consecutive(flag, timestamp_ms):
                return None
        
        return FlagDecision(
            flag=flag,
            phrase_key=phrase_key,
            priority=priority,
            confidence=result.confidence,
            source="steering"
        )
    
    def _check_consecutive(self, flag: CombinedFlag, timestamp_ms: int) -> bool:
        """
        Check if flag has been detected consecutively.
        
        Requires multiple consecutive detections within window
        to suppress single-frame false positives.
        """
        if flag not in self._detection_counts:
            self._detection_counts[flag] = []
        
        history = self._detection_counts[flag]
        
        # Clean old entries
        cutoff = timestamp_ms - self.config.detection_window_ms
        history[:] = [t for t in history if t > cutoff]
        
        # Add current detection
        history.append(timestamp_ms)
        
        # Check if enough consecutive
        return len(history) >= self.config.consecutive_detections_required
    
    def _should_output(self, decision: FlagDecision, timestamp_ms: int) -> bool:
        """Check if we should output this flag."""
        
        # Check corner limit
        if self._flags_this_corner >= self.config.max_flags_per_corner:
            # Allow critical to override
            if decision.flag not in [CombinedFlag.INSTABILITY, CombinedFlag.LIMIT]:
                return False
        
        # Check cooldown
        if timestamp_ms - self._last_flag_time_ms < self.config.flag_cooldown_ms:
            # Allow critical to override
            if decision.flag not in [CombinedFlag.INSTABILITY, CombinedFlag.LIMIT]:
                return False
        
        return True
    
    def new_lap(self) -> None:
        """Reset for new lap."""
        self._flags_this_corner = 0
        self._current_corner_id = -1
        self._detection_counts.clear()
    
    def reset(self) -> None:
        """Reset all state."""
        self._detection_counts.clear()
        self._last_flag_time_ms = 0
        self._flags_this_corner = 0
        self._current_corner_id = -1
