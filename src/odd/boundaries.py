"""
Boundary Enforcer
Safety-Critical Adaptive AI Race Coaching System

Enforces hard boundaries on system outputs.

SAFETY: Final gate before any output - enforces absolute limits.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum, auto


class BoundaryType(Enum):
    """Types of boundaries enforced."""
    
    SPEED_CEILING = auto()
    DECELERATION_CEILING = auto()
    LATERAL_G_CEILING = auto()
    COMBINED_G_CEILING = auto()
    CONFIDENCE_FLOOR = auto()


@dataclass
class BoundaryConfig:
    """Configuration for boundary enforcement."""
    
    # Speed limits
    absolute_max_speed_kmh: float = 350.0  # Physical impossibility check
    max_advised_speed_kmh: float = 300.0   # Never advise above this
    
    # Deceleration limits
    max_advised_decel_g: float = 1.5       # Never advise harder braking
    
    # Lateral limits
    max_advised_lateral_g: float = 1.5     # Never advise this lateral load
    
    # Combined limits
    max_advised_combined_g: float = 1.8    # Friction circle limit
    
    # Confidence
    min_confidence_for_output: float = 0.70
    min_confidence_for_advice: float = 0.85


@dataclass
class BoundaryCheck:
    """Result of a boundary check."""
    
    passed: bool
    boundary_type: BoundaryType
    original_value: float
    bounded_value: float
    message: str = ""


class BoundaryEnforcer:
    """
    Enforces absolute safety boundaries on system outputs.
    
    This is the FINAL safety gate before any value is used
    or communicated. It enforces physics-based absolute
    limits that should never be exceeded.
    
    SAFETY PRINCIPLE:
    - These are HARD limits, not suggestions
    - If a value exceeds limits, it's clamped or rejected
    - Boundary violations are always logged
    - This is defense-in-depth against upstream errors
    """
    
    def __init__(self, config: Optional[BoundaryConfig] = None):
        self.config = config or BoundaryConfig()
        self._violation_count = 0
        self._last_violations: list = []
    
    def check_speed(self, speed_kmh: float) -> BoundaryCheck:
        """
        Check speed value against boundaries.
        
        Args:
            speed_kmh: Speed value to check
            
        Returns:
            BoundaryCheck with result
        """
        if speed_kmh > self.config.absolute_max_speed_kmh:
            # This is a sensor error or calculation bug
            self._record_violation(BoundaryType.SPEED_CEILING, speed_kmh)
            return BoundaryCheck(
                passed=False,
                boundary_type=BoundaryType.SPEED_CEILING,
                original_value=speed_kmh,
                bounded_value=self.config.max_advised_speed_kmh,
                message=f"Speed {speed_kmh:.0f} km/h exceeds physical limit"
            )
        
        if speed_kmh > self.config.max_advised_speed_kmh:
            self._record_violation(BoundaryType.SPEED_CEILING, speed_kmh)
            return BoundaryCheck(
                passed=False,
                boundary_type=BoundaryType.SPEED_CEILING,
                original_value=speed_kmh,
                bounded_value=self.config.max_advised_speed_kmh,
                message=f"Speed {speed_kmh:.0f} km/h clamped to {self.config.max_advised_speed_kmh:.0f}"
            )
        
        return BoundaryCheck(
            passed=True,
            boundary_type=BoundaryType.SPEED_CEILING,
            original_value=speed_kmh,
            bounded_value=speed_kmh
        )
    
    def check_deceleration(self, decel_g: float) -> BoundaryCheck:
        """
        Check deceleration value against boundaries.
        
        Args:
            decel_g: Deceleration in G (positive = braking)
            
        Returns:
            BoundaryCheck with result
        """
        if decel_g > self.config.max_advised_decel_g:
            self._record_violation(BoundaryType.DECELERATION_CEILING, decel_g)
            return BoundaryCheck(
                passed=False,
                boundary_type=BoundaryType.DECELERATION_CEILING,
                original_value=decel_g,
                bounded_value=self.config.max_advised_decel_g,
                message=f"Decel {decel_g:.2f}g exceeds limit"
            )
        
        return BoundaryCheck(
            passed=True,
            boundary_type=BoundaryType.DECELERATION_CEILING,
            original_value=decel_g,
            bounded_value=decel_g
        )
    
    def check_lateral_g(self, lateral_g: float) -> BoundaryCheck:
        """
        Check lateral G value against boundaries.
        
        Args:
            lateral_g: Lateral acceleration in G
            
        Returns:
            BoundaryCheck with result
        """
        if abs(lateral_g) > self.config.max_advised_lateral_g:
            self._record_violation(BoundaryType.LATERAL_G_CEILING, lateral_g)
            return BoundaryCheck(
                passed=False,
                boundary_type=BoundaryType.LATERAL_G_CEILING,
                original_value=lateral_g,
                bounded_value=self.config.max_advised_lateral_g,
                message=f"Lateral {lateral_g:.2f}g exceeds limit"
            )
        
        return BoundaryCheck(
            passed=True,
            boundary_type=BoundaryType.LATERAL_G_CEILING,
            original_value=lateral_g,
            bounded_value=lateral_g
        )
    
    def check_combined_g(self, longitudinal_g: float, lateral_g: float) -> BoundaryCheck:
        """
        Check combined G (friction circle) against boundaries.
        
        Args:
            longitudinal_g: Longitudinal acceleration
            lateral_g: Lateral acceleration
            
        Returns:
            BoundaryCheck with result
        """
        import math
        combined = math.sqrt(longitudinal_g**2 + lateral_g**2)
        
        if combined > self.config.max_advised_combined_g:
            self._record_violation(BoundaryType.COMBINED_G_CEILING, combined)
            return BoundaryCheck(
                passed=False,
                boundary_type=BoundaryType.COMBINED_G_CEILING,
                original_value=combined,
                bounded_value=self.config.max_advised_combined_g,
                message=f"Combined {combined:.2f}g exceeds friction circle"
            )
        
        return BoundaryCheck(
            passed=True,
            boundary_type=BoundaryType.COMBINED_G_CEILING,
            original_value=combined,
            bounded_value=combined
        )
    
    def check_confidence(self, confidence: float, for_advice: bool = True) -> BoundaryCheck:
        """
        Check confidence value against minimum.
        
        Args:
            confidence: Confidence value (0-1)
            for_advice: Whether this is for giving advice (stricter)
            
        Returns:
            BoundaryCheck with result
        """
        threshold = (self.config.min_confidence_for_advice if for_advice 
                    else self.config.min_confidence_for_output)
        
        if confidence < threshold:
            self._record_violation(BoundaryType.CONFIDENCE_FLOOR, confidence)
            return BoundaryCheck(
                passed=False,
                boundary_type=BoundaryType.CONFIDENCE_FLOOR,
                original_value=confidence,
                bounded_value=0.0,  # Zero confidence output
                message=f"Confidence {confidence:.0%} below threshold {threshold:.0%}"
            )
        
        return BoundaryCheck(
            passed=True,
            boundary_type=BoundaryType.CONFIDENCE_FLOOR,
            original_value=confidence,
            bounded_value=confidence
        )
    
    def clamp_speed(self, speed_kmh: float) -> float:
        """Clamp speed to safe range."""
        return min(speed_kmh, self.config.max_advised_speed_kmh)
    
    def clamp_deceleration(self, decel_g: float) -> float:
        """Clamp deceleration to safe range."""
        return min(decel_g, self.config.max_advised_decel_g)
    
    def clamp_lateral_g(self, lateral_g: float) -> float:
        """Clamp lateral G to safe range."""
        sign = 1 if lateral_g >= 0 else -1
        return sign * min(abs(lateral_g), self.config.max_advised_lateral_g)
    
    def _record_violation(self, boundary_type: BoundaryType, value: float) -> None:
        """Record a boundary violation."""
        self._violation_count += 1
        self._last_violations.append({
            "type": boundary_type,
            "value": value,
            "count": self._violation_count
        })
        
        # Keep only recent violations
        if len(self._last_violations) > 100:
            self._last_violations.pop(0)
    
    @property
    def violation_count(self) -> int:
        """Get total violation count."""
        return self._violation_count
    
    def get_recent_violations(self) -> list:
        """Get recent violations."""
        return list(self._last_violations)
    
    def reset_counters(self) -> None:
        """Reset violation counters."""
        self._violation_count = 0
        self._last_violations.clear()
