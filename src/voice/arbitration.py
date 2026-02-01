"""
Voice Arbitration Engine
Safety-Critical Adaptive AI Race Coaching System

Decides what voice output should be spoken and when.

SAFETY INVARIANTS:
- S1: Silence is always safer than incorrect advice
- S5: Voice output is deterministic and finite
- S6: Mid-corner speech is forbidden unless instability imminent

GOVERNING PRINCIPLE: Silence wins by default.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Tuple
import time

from ..types.geometry import CornerPhase
from ..types.confidence import Confidence
from .phrase_dictionary import PhraseDictionary, PhraseKey, Phrase
from .cognitive_model import CognitiveLoadModel, CognitiveState


class VoiceAction(Enum):
    """Actions the voice system can take."""
    
    SPEAK = auto()     # Speak the message
    SUPPRESS = auto()  # Suppress the message (silence)
    QUEUE = auto()     # Queue for later
    ABORT = auto()     # Abort current speech


@dataclass
class VoiceRequest:
    """Request to speak a phrase."""
    
    phrase_key: PhraseKey
    timestamp_ms: int
    confidence: float  # Confidence in the advice (0-1)
    segment_id: int = 0
    corner_id: int = 0
    
    # Metadata
    source: str = ""  # e.g., "braking_detector", "speed_monitor"
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical safety message."""
        return self.phrase_key in [
            PhraseKey.INSTABILITY,
            PhraseKey.LIMIT
        ]


@dataclass
class VoiceDecision:
    """Decision made by the arbitration engine."""
    
    action: VoiceAction
    phrase_key: Optional[PhraseKey] = None
    phrase_text: Optional[str] = None
    reason: str = ""
    timestamp_ms: int = 0


@dataclass
class ArbitrationConfig:
    """Configuration for voice arbitration."""
    
    # Confidence threshold for voice output
    min_confidence_to_speak: float = 0.85
    
    # Priority thresholds
    # Only speak if priority is at or below this level
    max_allowed_priority: int = 3
    
    # Queue settings
    max_queue_size: int = 3
    max_queue_age_ms: int = 2000  # Discard queued items older than this
    
    # Abort settings
    abort_on_phase_change: bool = True
    abort_on_confidence_drop: bool = True
    confidence_drop_threshold: float = 0.2


class VoiceArbitrationEngine:
    """
    Decides what voice output should be spoken.
    
    This is the gatekeeper for all voice output. It enforces:
    - Confidence thresholds
    - Cognitive load restrictions
    - Phase-appropriate speech
    - Priority arbitration
    - Message suppression
    
    GOVERNING PRINCIPLE: Silence wins by default.
    
    If there is any doubt about whether to speak, the answer is NO.
    """
    
    def __init__(
        self,
        config: Optional[ArbitrationConfig] = None,
        phrase_dictionary: Optional[PhraseDictionary] = None,
        cognitive_model: Optional[CognitiveLoadModel] = None
    ):
        self.config = config or ArbitrationConfig()
        self.phrases = phrase_dictionary or PhraseDictionary()
        self.cognitive = cognitive_model or CognitiveLoadModel()
        
        # State
        self._pending_requests: List[VoiceRequest] = []
        self._last_spoken_key: Optional[PhraseKey] = None
        self._last_spoken_time_ms: int = 0
        self._current_phase: CornerPhase = CornerPhase.STRAIGHT
        self._is_speaking: bool = False
    
    def submit_request(self, request: VoiceRequest) -> VoiceDecision:
        """
        Submit a voice request for arbitration.
        
        Args:
            request: Voice request to evaluate
            
        Returns:
            Decision on whether to speak
        """
        # Get phrase details
        try:
            phrase = self.phrases.get(request.phrase_key)
        except KeyError:
            return VoiceDecision(
                action=VoiceAction.SUPPRESS,
                reason="unknown_phrase_key",
                timestamp_ms=request.timestamp_ms
            )
        
        # === GATE 1: Confidence Check ===
        # SAFETY INVARIANT S1: Low confidence = silence
        if request.confidence < self.config.min_confidence_to_speak:
            return VoiceDecision(
                action=VoiceAction.SUPPRESS,
                reason=f"low_confidence:{request.confidence:.2f}",
                timestamp_ms=request.timestamp_ms
            )
        
        # === GATE 2: Phase Check ===
        # SAFETY INVARIANT S6: Apex = no speech (unless critical)
        phase_name = self._current_phase.name.lower()
        
        if not self.phrases.is_allowed_in_phase(request.phrase_key, phase_name):
            if request.is_critical and phrase.may_interrupt:
                pass  # Critical can override phase restriction
            else:
                return VoiceDecision(
                    action=VoiceAction.SUPPRESS,
                    reason=f"phase_not_allowed:{phase_name}",
                    timestamp_ms=request.timestamp_ms
                )
        
        # === GATE 3: Cognitive Load Check ===
        cognitive_state = self.cognitive.compute_load(
            phase=self._current_phase,
            speed_kmh=100.0,  # Would come from telemetry
            lateral_g=0.5,    # Would come from telemetry
            current_timestamp_ms=request.timestamp_ms,
            corner_id=request.corner_id
        )
        
        can_speak, reason = self.cognitive.can_speak(
            cognitive_state,
            is_critical=request.is_critical
        )
        
        if not can_speak:
            return VoiceDecision(
                action=VoiceAction.SUPPRESS,
                reason=f"cognitive_load:{reason}",
                timestamp_ms=request.timestamp_ms
            )
        
        # === GATE 4: Priority Check ===
        if phrase.priority > self.config.max_allowed_priority:
            if not request.is_critical:
                return VoiceDecision(
                    action=VoiceAction.SUPPRESS,
                    reason=f"low_priority:{phrase.priority}",
                    timestamp_ms=request.timestamp_ms
                )
        
        # === GATE 5: Conflict Resolution ===
        if self._is_speaking:
            if phrase.may_interrupt:
                return VoiceDecision(
                    action=VoiceAction.SPEAK,
                    phrase_key=request.phrase_key,
                    phrase_text=phrase.text,
                    reason="interrupt",
                    timestamp_ms=request.timestamp_ms
                )
            else:
                # Queue for later
                self._add_to_queue(request)
                return VoiceDecision(
                    action=VoiceAction.QUEUE,
                    phrase_key=request.phrase_key,
                    reason="queued_behind_active",
                    timestamp_ms=request.timestamp_ms
                )
        
        # === GATE 6: Duplicate Check ===
        if (self._last_spoken_key == request.phrase_key and
            request.timestamp_ms - self._last_spoken_time_ms < 5000):
            return VoiceDecision(
                action=VoiceAction.SUPPRESS,
                reason="duplicate_recent",
                timestamp_ms=request.timestamp_ms
            )
        
        # === ALL GATES PASSED: Approve Speech ===
        self.cognitive.record_message(request.timestamp_ms)
        self._last_spoken_key = request.phrase_key
        self._last_spoken_time_ms = request.timestamp_ms
        
        return VoiceDecision(
            action=VoiceAction.SPEAK,
            phrase_key=request.phrase_key,
            phrase_text=phrase.text,
            reason="approved",
            timestamp_ms=request.timestamp_ms
        )
    
    def update_phase(self, phase: CornerPhase) -> Optional[VoiceDecision]:
        """
        Update current corner phase.
        
        May trigger abort of current speech if phase changed to apex.
        """
        old_phase = self._current_phase
        self._current_phase = phase
        
        # Check if we need to abort current speech
        if (self.config.abort_on_phase_change and
            self._is_speaking and
            phase == CornerPhase.APEX and
            old_phase != CornerPhase.APEX):
            
            return VoiceDecision(
                action=VoiceAction.ABORT,
                reason="phase_changed_to_apex",
                timestamp_ms=int(time.time() * 1000)
            )
        
        return None
    
    def update_confidence(self, confidence: float) -> Optional[VoiceDecision]:
        """
        Update system confidence.
        
        May trigger abort if confidence dropped significantly.
        """
        # This would compare to previous confidence
        # For now, just check absolute threshold
        if (self.config.abort_on_confidence_drop and
            self._is_speaking and
            confidence < self.config.min_confidence_to_speak):
            
            return VoiceDecision(
                action=VoiceAction.ABORT,
                reason="confidence_dropped",
                timestamp_ms=int(time.time() * 1000)
            )
        
        return None
    
    def get_next_queued(self) -> Optional[VoiceRequest]:
        """Get next queued request (if any)."""
        
        if not self._pending_requests:
            return None
        
        now_ms = int(time.time() * 1000)
        
        # Remove stale requests
        self._pending_requests = [
            r for r in self._pending_requests
            if now_ms - r.timestamp_ms < self.config.max_queue_age_ms
        ]
        
        if not self._pending_requests:
            return None
        
        # Return highest priority request
        self._pending_requests.sort(
            key=lambda r: self.phrases.get(r.phrase_key).priority
        )
        
        return self._pending_requests.pop(0)
    
    def _add_to_queue(self, request: VoiceRequest) -> None:
        """Add request to queue."""
        
        if len(self._pending_requests) >= self.config.max_queue_size:
            # Remove lowest priority
            self._pending_requests.sort(
                key=lambda r: self.phrases.get(r.phrase_key).priority,
                reverse=True
            )
            self._pending_requests.pop()
        
        self._pending_requests.append(request)
    
    def mark_speaking_started(self) -> None:
        """Mark that TTS has started speaking."""
        self._is_speaking = True
    
    def mark_speaking_finished(self) -> None:
        """Mark that TTS has finished speaking."""
        self._is_speaking = False
    
    def new_lap(self) -> None:
        """Reset for new lap."""
        self.cognitive.new_lap()
        self._pending_requests.clear()
    
    def reset(self) -> None:
        """Reset all state."""
        self.cognitive.reset()
        self._pending_requests.clear()
        self._last_spoken_key = None
        self._last_spoken_time_ms = 0
        self._current_phase = CornerPhase.STRAIGHT
        self._is_speaking = False
    
    def get_stats(self) -> dict:
        """Get arbitration statistics."""
        return {
            "is_speaking": self._is_speaking,
            "queue_size": len(self._pending_requests),
            "current_phase": self._current_phase.name,
            "last_spoken_key": self._last_spoken_key.name if self._last_spoken_key else None
        }
