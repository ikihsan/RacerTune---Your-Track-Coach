"""
Phrase Dictionary
Safety-Critical Adaptive AI Race Coaching System

Fixed, immutable phrase dictionary for voice output.

SAFETY INVARIANT S5: Voice output is deterministic and finite.
All voice output MUST come from this dictionary.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, List, Set
import yaml


class PhraseKey(Enum):
    """
    Keys for all allowed voice phrases.
    
    SAFETY: Adding new phrases requires safety review.
    """
    
    # Braking
    BRAKE_EARLIER = auto()
    BRAKE_NOW = auto()
    TRAIL_BRAKE = auto()
    BRAKE_LIGHTER = auto()
    
    # Steering
    SMOOTH_INPUTS = auto()
    OPEN_STEERING = auto()
    HOLD_LINE = auto()
    
    # Speed
    ENTRY_SPEED_HIGH = auto()
    SLOW_IN = auto()
    CARRY_SPEED = auto()
    
    # Throttle
    POWER = auto()
    EASY_THROTTLE = auto()
    WAIT_THROTTLE = auto()
    
    # Critical warnings
    INSTABILITY = auto()
    LIMIT = auto()
    SURFACE = auto()
    
    # Corners
    TURN_1 = auto()
    TURN_2 = auto()
    TURN_3 = auto()
    TURN_4 = auto()
    TURN_5 = auto()
    HAIRPIN = auto()
    CHICANE = auto()
    ESSES = auto()
    
    # Distance
    FIFTY_M = auto()
    HUNDRED_M = auto()
    TWO_HUNDRED_M = auto()
    
    # Post-lap
    GOOD_LAP = auto()
    PERSONAL_BEST = auto()
    CONSISTENT = auto()
    BRAKING_IMPROVED = auto()
    ENTRY_IMPROVED = auto()
    
    # System
    SYSTEM_READY = auto()
    RECORDING = auto()
    LAP_RECORDED = auto()
    LOW_CONFIDENCE = auto()
    SYSTEM_SILENT = auto()


@dataclass(frozen=True)
class Phrase:
    """
    Immutable voice phrase.
    
    All properties are fixed at creation.
    """
    
    key: PhraseKey
    text: str
    priority: int  # 0 = highest (critical), 5 = lowest (background)
    allowed_phases: frozenset  # Corner phases where this can be spoken
    may_interrupt: bool = False  # Can interrupt other speech
    
    def __post_init__(self):
        # Validate text length (must be speakable in <3 seconds)
        # Rough estimate: 3 words per second
        word_count = len(self.text.split())
        if word_count > 6:
            raise ValueError(f"Phrase too long: {self.text}")


class PhraseDictionary:
    """
    Immutable dictionary of allowed voice phrases.
    
    SAFETY INVARIANT S5:
    - All phrases are pre-defined
    - No dynamic text generation
    - No string concatenation
    - Dictionary is immutable at runtime
    """
    
    # The complete phrase dictionary
    # SAFETY: This is the ONLY source of voice output text
    _PHRASES = {
        # Braking
        PhraseKey.BRAKE_EARLIER: Phrase(
            key=PhraseKey.BRAKE_EARLIER,
            text="Brake earlier",
            priority=2,
            allowed_phases=frozenset(["approach"])
        ),
        PhraseKey.BRAKE_NOW: Phrase(
            key=PhraseKey.BRAKE_NOW,
            text="Brake",
            priority=1,
            allowed_phases=frozenset(["approach", "entry"])
        ),
        PhraseKey.TRAIL_BRAKE: Phrase(
            key=PhraseKey.TRAIL_BRAKE,
            text="Trail brake",
            priority=3,
            allowed_phases=frozenset(["entry"])
        ),
        PhraseKey.BRAKE_LIGHTER: Phrase(
            key=PhraseKey.BRAKE_LIGHTER,
            text="Lighter braking",
            priority=3,
            allowed_phases=frozenset(["approach"])
        ),
        
        # Steering
        PhraseKey.SMOOTH_INPUTS: Phrase(
            key=PhraseKey.SMOOTH_INPUTS,
            text="Smooth inputs",
            priority=2,
            allowed_phases=frozenset(["entry", "exit"])
        ),
        PhraseKey.OPEN_STEERING: Phrase(
            key=PhraseKey.OPEN_STEERING,
            text="Open steering",
            priority=3,
            allowed_phases=frozenset(["exit"])
        ),
        PhraseKey.HOLD_LINE: Phrase(
            key=PhraseKey.HOLD_LINE,
            text="Hold line",
            priority=2,
            allowed_phases=frozenset(["apex", "exit"])
        ),
        
        # Speed
        PhraseKey.ENTRY_SPEED_HIGH: Phrase(
            key=PhraseKey.ENTRY_SPEED_HIGH,
            text="Entry speed",
            priority=2,
            allowed_phases=frozenset(["approach"])
        ),
        PhraseKey.SLOW_IN: Phrase(
            key=PhraseKey.SLOW_IN,
            text="Slow in",
            priority=2,
            allowed_phases=frozenset(["approach"])
        ),
        PhraseKey.CARRY_SPEED: Phrase(
            key=PhraseKey.CARRY_SPEED,
            text="Carry speed",
            priority=3,
            allowed_phases=frozenset(["exit"])
        ),
        
        # Throttle
        PhraseKey.POWER: Phrase(
            key=PhraseKey.POWER,
            text="Power",
            priority=3,
            allowed_phases=frozenset(["exit"])
        ),
        PhraseKey.EASY_THROTTLE: Phrase(
            key=PhraseKey.EASY_THROTTLE,
            text="Easy throttle",
            priority=2,
            allowed_phases=frozenset(["exit"])
        ),
        PhraseKey.WAIT_THROTTLE: Phrase(
            key=PhraseKey.WAIT_THROTTLE,
            text="Wait for throttle",
            priority=2,
            allowed_phases=frozenset(["apex"])
        ),
        
        # Critical warnings
        PhraseKey.INSTABILITY: Phrase(
            key=PhraseKey.INSTABILITY,
            text="Careful",
            priority=0,
            allowed_phases=frozenset(["approach", "entry", "apex", "exit"]),
            may_interrupt=True
        ),
        PhraseKey.LIMIT: Phrase(
            key=PhraseKey.LIMIT,
            text="Limit",
            priority=0,
            allowed_phases=frozenset(["approach", "entry", "apex", "exit"]),
            may_interrupt=True
        ),
        PhraseKey.SURFACE: Phrase(
            key=PhraseKey.SURFACE,
            text="Surface",
            priority=1,
            allowed_phases=frozenset(["approach"])
        ),
        
        # Corners
        PhraseKey.TURN_1: Phrase(
            key=PhraseKey.TURN_1,
            text="Turn one",
            priority=4,
            allowed_phases=frozenset(["straight"])
        ),
        PhraseKey.TURN_2: Phrase(
            key=PhraseKey.TURN_2,
            text="Turn two",
            priority=4,
            allowed_phases=frozenset(["straight"])
        ),
        PhraseKey.TURN_3: Phrase(
            key=PhraseKey.TURN_3,
            text="Turn three",
            priority=4,
            allowed_phases=frozenset(["straight"])
        ),
        PhraseKey.HAIRPIN: Phrase(
            key=PhraseKey.HAIRPIN,
            text="Hairpin",
            priority=4,
            allowed_phases=frozenset(["straight"])
        ),
        PhraseKey.CHICANE: Phrase(
            key=PhraseKey.CHICANE,
            text="Chicane",
            priority=4,
            allowed_phases=frozenset(["straight"])
        ),
        
        # Distance
        PhraseKey.FIFTY_M: Phrase(
            key=PhraseKey.FIFTY_M,
            text="Fifty",
            priority=3,
            allowed_phases=frozenset(["straight", "approach"])
        ),
        PhraseKey.HUNDRED_M: Phrase(
            key=PhraseKey.HUNDRED_M,
            text="Hundred",
            priority=3,
            allowed_phases=frozenset(["straight", "approach"])
        ),
        
        # Post-lap
        PhraseKey.GOOD_LAP: Phrase(
            key=PhraseKey.GOOD_LAP,
            text="Good lap",
            priority=5,
            allowed_phases=frozenset(["pit", "cooldown"])
        ),
        PhraseKey.PERSONAL_BEST: Phrase(
            key=PhraseKey.PERSONAL_BEST,
            text="Personal best",
            priority=5,
            allowed_phases=frozenset(["pit", "cooldown"])
        ),
        PhraseKey.CONSISTENT: Phrase(
            key=PhraseKey.CONSISTENT,
            text="Consistent",
            priority=5,
            allowed_phases=frozenset(["pit", "cooldown"])
        ),
        
        # System
        PhraseKey.SYSTEM_READY: Phrase(
            key=PhraseKey.SYSTEM_READY,
            text="System ready",
            priority=5,
            allowed_phases=frozenset(["pit"])
        ),
        PhraseKey.RECORDING: Phrase(
            key=PhraseKey.RECORDING,
            text="Recording",
            priority=5,
            allowed_phases=frozenset(["pit"])
        ),
        PhraseKey.LAP_RECORDED: Phrase(
            key=PhraseKey.LAP_RECORDED,
            text="Lap recorded",
            priority=5,
            allowed_phases=frozenset(["straight", "pit"])
        ),
        PhraseKey.LOW_CONFIDENCE: Phrase(
            key=PhraseKey.LOW_CONFIDENCE,
            text="Low confidence",
            priority=4,
            allowed_phases=frozenset(["pit"])
        ),
        PhraseKey.SYSTEM_SILENT: Phrase(
            key=PhraseKey.SYSTEM_SILENT,
            text="Going silent",
            priority=4,
            allowed_phases=frozenset(["pit", "straight"])
        ),
    }
    
    def __init__(self):
        # Validate all phrases at initialization
        self._validate_dictionary()
    
    def _validate_dictionary(self) -> None:
        """Validate phrase dictionary integrity."""
        
        # Check all PhraseKeys have entries
        for key in PhraseKey:
            if key not in self._PHRASES:
                raise RuntimeError(f"Missing phrase for key: {key}")
    
    def get(self, key: PhraseKey) -> Phrase:
        """
        Get a phrase by key.
        
        SAFETY: Only returns pre-defined phrases.
        """
        if key not in self._PHRASES:
            raise KeyError(f"Unknown phrase key: {key}")
        
        return self._PHRASES[key]
    
    def get_text(self, key: PhraseKey) -> str:
        """Get phrase text by key."""
        return self.get(key).text
    
    def get_priority(self, key: PhraseKey) -> int:
        """Get phrase priority by key."""
        return self.get(key).priority
    
    def is_allowed_in_phase(self, key: PhraseKey, phase: str) -> bool:
        """Check if phrase is allowed in given corner phase."""
        phrase = self.get(key)
        return phase.lower() in phrase.allowed_phases
    
    def get_critical_phrases(self) -> List[PhraseKey]:
        """Get all critical (priority 0) phrases."""
        return [
            key for key, phrase in self._PHRASES.items()
            if phrase.priority == 0
        ]
    
    def can_interrupt(self, key: PhraseKey) -> bool:
        """Check if phrase can interrupt other speech."""
        return self.get(key).may_interrupt
    
    @classmethod
    def get_all_phrases(cls) -> List[Phrase]:
        """Get all phrases (for validation/testing)."""
        return list(cls._PHRASES.values())
    
    @classmethod
    def get_all_keys(cls) -> List[PhraseKey]:
        """Get all phrase keys."""
        return list(cls._PHRASES.keys())
