"""
Confidence Scoring Types
Safety-Critical Adaptive AI Race Coaching System

This module defines the confidence model used throughout the system.
Confidence propagates through all computations and gates safety-critical decisions.

SAFETY INVARIANT: Low confidence must propagate to silence, not guessing.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List
import math


class ConfidenceLevel(Enum):
    """Discrete confidence levels for system-wide decisions."""
    
    VERY_HIGH = auto()   # >= 0.95 - Full operation
    HIGH = auto()        # >= 0.85 - Voice enabled
    MEDIUM = auto()      # >= 0.70 - Limited voice, no learning
    LOW = auto()         # >= 0.50 - Silent mode
    VERY_LOW = auto()    # >= 0.30 - Recording only
    INVALID = auto()     # < 0.30 - Cannot operate
    
    @classmethod
    def from_value(cls, value: float) -> "ConfidenceLevel":
        """Convert numeric confidence to discrete level."""
        if value >= 0.95:
            return cls.VERY_HIGH
        elif value >= 0.85:
            return cls.HIGH
        elif value >= 0.70:
            return cls.MEDIUM
        elif value >= 0.50:
            return cls.LOW
        elif value >= 0.30:
            return cls.VERY_LOW
        else:
            return cls.INVALID


@dataclass(frozen=True)
class Confidence:
    """
    Immutable confidence score with metadata.
    
    SAFETY: Confidence values are clamped to [0, 1].
    SAFETY: Lower bound confidence propagates in fusion operations.
    """
    
    value: float
    source: str
    timestamp_ms: int
    degradation_reason: Optional[str] = None
    
    def __post_init__(self):
        # Clamp to valid range
        object.__setattr__(self, 'value', max(0.0, min(1.0, self.value)))
    
    @property
    def level(self) -> ConfidenceLevel:
        """Get discrete confidence level."""
        return ConfidenceLevel.from_value(self.value)
    
    @property
    def allows_voice(self) -> bool:
        """Check if confidence is sufficient for voice output."""
        return self.value >= 0.85
    
    @property
    def allows_learning(self) -> bool:
        """Check if confidence is sufficient for learning contribution."""
        return self.value >= 0.90
    
    @property
    def allows_operation(self) -> bool:
        """Check if confidence is sufficient for any operation."""
        return self.value >= 0.30
    
    def degrade(self, factor: float, reason: str) -> "Confidence":
        """
        Create degraded confidence.
        
        Args:
            factor: Multiplication factor (0-1)
            reason: Reason for degradation
            
        Returns:
            New Confidence with reduced value
        """
        new_value = self.value * max(0.0, min(1.0, factor))
        combined_reason = f"{self.degradation_reason}; {reason}" if self.degradation_reason else reason
        return Confidence(
            value=new_value,
            source=self.source,
            timestamp_ms=self.timestamp_ms,
            degradation_reason=combined_reason
        )


@dataclass(frozen=True)
class ConfidenceVector:
    """
    Multi-dimensional confidence for complex systems.
    
    Each component represents confidence in a different aspect.
    The minimum component determines overall system confidence.
    """
    
    gps_confidence: Confidence
    imu_confidence: Confidence
    geometry_confidence: Confidence
    physics_confidence: Confidence
    
    @property
    def overall(self) -> Confidence:
        """
        Compute overall confidence as minimum of components.
        
        SAFETY: We use MIN, not average, because any weak link
        can cause system failure.
        """
        components = [
            self.gps_confidence,
            self.imu_confidence,
            self.geometry_confidence,
            self.physics_confidence
        ]
        
        min_conf = min(components, key=lambda c: c.value)
        
        return Confidence(
            value=min_conf.value,
            source="combined",
            timestamp_ms=min_conf.timestamp_ms,
            degradation_reason=f"Limited by {min_conf.source}: {min_conf.degradation_reason}"
        )
    
    @property
    def level(self) -> ConfidenceLevel:
        """Get discrete level from overall confidence."""
        return self.overall.level


def fuse_confidence(
    confidences: List[Confidence],
    method: str = "minimum"
) -> Confidence:
    """
    Fuse multiple confidence values.
    
    SAFETY: Default method is 'minimum' (most conservative).
    
    Args:
        confidences: List of confidence values to fuse
        method: Fusion method ('minimum', 'weighted', 'geometric')
        
    Returns:
        Fused confidence value
    """
    if not confidences:
        return Confidence(
            value=0.0,
            source="empty",
            timestamp_ms=0,
            degradation_reason="No confidence sources"
        )
    
    if method == "minimum":
        # Most conservative: use lowest confidence
        min_conf = min(confidences, key=lambda c: c.value)
        return Confidence(
            value=min_conf.value,
            source="fused_min",
            timestamp_ms=max(c.timestamp_ms for c in confidences),
            degradation_reason=min_conf.degradation_reason
        )
    
    elif method == "geometric":
        # Geometric mean - punishes low values more than arithmetic
        product = 1.0
        for c in confidences:
            product *= c.value
        geo_mean = product ** (1.0 / len(confidences))
        
        return Confidence(
            value=geo_mean,
            source="fused_geometric",
            timestamp_ms=max(c.timestamp_ms for c in confidences),
            degradation_reason=None
        )
    
    elif method == "weighted":
        # Weighted by individual confidence (higher confidence = more weight)
        total_weight = sum(c.value for c in confidences)
        if total_weight == 0:
            return Confidence(
                value=0.0,
                source="fused_weighted",
                timestamp_ms=max(c.timestamp_ms for c in confidences),
                degradation_reason="All sources have zero confidence"
            )
        
        weighted_sum = sum(c.value * c.value for c in confidences)
        weighted_avg = weighted_sum / total_weight
        
        return Confidence(
            value=weighted_avg,
            source="fused_weighted",
            timestamp_ms=max(c.timestamp_ms for c in confidences),
            degradation_reason=None
        )
    
    else:
        raise ValueError(f"Unknown fusion method: {method}")


@dataclass
class ConfidenceTracker:
    """
    Tracks confidence over time for trend analysis.
    
    Used to detect confidence degradation that may require
    system mode changes.
    """
    
    history: List[Confidence] = field(default_factory=list)
    max_history: int = 100
    
    def add(self, confidence: Confidence) -> None:
        """Add a confidence observation."""
        self.history.append(confidence)
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    @property
    def current(self) -> Optional[Confidence]:
        """Get most recent confidence."""
        return self.history[-1] if self.history else None
    
    @property
    def trend(self) -> float:
        """
        Compute confidence trend.
        
        Returns:
            Positive = improving, Negative = degrading, 0 = stable
        """
        if len(self.history) < 10:
            return 0.0
        
        recent = self.history[-10:]
        older = self.history[-20:-10] if len(self.history) >= 20 else self.history[:10]
        
        recent_avg = sum(c.value for c in recent) / len(recent)
        older_avg = sum(c.value for c in older) / len(older)
        
        return recent_avg - older_avg
    
    @property
    def is_degrading(self) -> bool:
        """Check if confidence is trending downward."""
        return self.trend < -0.1
    
    @property
    def is_stable(self) -> bool:
        """Check if confidence is stable."""
        return abs(self.trend) < 0.05
    
    def reset(self) -> None:
        """Clear confidence history."""
        self.history.clear()
