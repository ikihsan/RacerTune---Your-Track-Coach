"""
Physics Envelope Types
Safety-Critical Adaptive AI Race Coaching System

This module defines physics-based controllability envelopes.

SAFETY INVARIANT S2: Physics envelopes are HARD CEILINGS.
No learned value, user input, or optimization may exceed these limits.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Tuple
import math

from .confidence import Confidence


class EnvelopeType(Enum):
    """Types of controllability envelopes."""
    CORNER_SPEED = auto()       # Maximum controllable corner speed
    BRAKING = auto()            # Braking deceleration limits
    STEERING = auto()           # Steering intensity limits
    COMBINED_GRIP = auto()      # Friction circle limits
    ACCELERATION = auto()       # Acceleration limits


@dataclass(frozen=True)
class PhysicsCeiling:
    """
    Immutable physics ceiling value.
    
    SAFETY: This value cannot be exceeded by any downstream computation.
    The value is set at initialization and cannot be modified.
    """
    
    value: float
    unit: str
    source: str  # "tire_model", "vehicle_config", "measured"
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Physics ceiling cannot be negative")
    
    def apply_safety_margin(self, margin: float) -> "PhysicsCeiling":
        """
        Create new ceiling with safety margin applied.
        
        Args:
            margin: Safety factor (0-1), e.g., 0.85 = 15% margin
            
        Returns:
            New PhysicsCeiling with reduced value
        """
        if not 0 < margin <= 1:
            raise ValueError(f"Safety margin must be in (0, 1], got {margin}")
        
        return PhysicsCeiling(
            value=self.value * margin,
            unit=self.unit,
            source=f"{self.source}_with_margin"
        )


@dataclass(frozen=True)
class CornerSpeedEnvelope:
    """
    Speed envelope for a track segment.
    
    Defines maximum controllable speed based on physics.
    """
    
    segment_id: int
    distance_start_m: float
    distance_end_m: float
    
    # Physics ceiling - CANNOT BE EXCEEDED
    physics_ceiling_kmh: PhysicsCeiling = field(
        default_factory=lambda: PhysicsCeiling(300.0, "km/h", "default")
    )
    
    # Conservative default (with safety margin)
    conservative_speed_kmh: float = 100.0
    
    # Learned adjustment (if available)
    learned_speed_kmh: Optional[float] = None
    learning_confidence: float = 0.0
    
    # Final blended speed
    envelope_speed_kmh: float = 100.0
    
    # Corner geometry
    corner_radius_m: float = float('inf')
    curvature_1_per_m: float = 0.0
    
    # Confidence
    confidence: Confidence = field(
        default_factory=lambda: Confidence(0.5, "envelope", 0)
    )
    
    def __post_init__(self):
        # SAFETY INVARIANT S2: Enforce ceiling
        if self.envelope_speed_kmh > self.physics_ceiling_kmh.value:
            object.__setattr__(
                self,
                'envelope_speed_kmh',
                self.physics_ceiling_kmh.value
            )
    
    @staticmethod
    def compute_physics_limit(
        radius_m: float,
        friction_mu: float = 1.0,
        safety_factor: float = 0.85
    ) -> float:
        """
        Compute physics-limited corner speed.
        
        Formula: v = sqrt(g * mu * r) * safety_factor
        
        Args:
            radius_m: Corner radius
            friction_mu: Tire friction coefficient
            safety_factor: Safety margin (default 15%)
            
        Returns:
            Maximum controllable speed in km/h
        """
        if radius_m <= 0 or radius_m == float('inf'):
            return 300.0  # Straight line limit
        
        G = 9.81  # m/s^2
        
        # v = sqrt(g * mu * r)
        v_m_s = math.sqrt(G * friction_mu * radius_m)
        
        # Apply safety factor
        v_m_s *= safety_factor
        
        # Convert to km/h
        v_kmh = v_m_s * 3.6
        
        return v_kmh
    
    def blend_with_learned(
        self,
        learned_speed_kmh: float,
        blend_weight: float
    ) -> "CornerSpeedEnvelope":
        """
        Create new envelope blended with learned data.
        
        SAFETY: Result is always clamped to physics ceiling.
        
        Args:
            learned_speed_kmh: Speed from observed laps
            blend_weight: Weight for learned value (0-1)
            
        Returns:
            New envelope with blended speed
        """
        # Clamp blend weight
        weight = max(0.0, min(0.3, blend_weight))  # Max 30% learned influence
        
        # Blend conservatively
        blended = (1.0 - weight) * self.conservative_speed_kmh + weight * learned_speed_kmh
        
        # SAFETY: Clamp to physics ceiling
        final = min(blended, self.physics_ceiling_kmh.value)
        
        return CornerSpeedEnvelope(
            segment_id=self.segment_id,
            distance_start_m=self.distance_start_m,
            distance_end_m=self.distance_end_m,
            physics_ceiling_kmh=self.physics_ceiling_kmh,
            conservative_speed_kmh=self.conservative_speed_kmh,
            learned_speed_kmh=learned_speed_kmh,
            learning_confidence=blend_weight,
            envelope_speed_kmh=final,
            corner_radius_m=self.corner_radius_m,
            curvature_1_per_m=self.curvature_1_per_m,
            confidence=self.confidence
        )


@dataclass(frozen=True)
class BrakingEnvelope:
    """
    Braking envelope for a segment.
    
    Defines maximum controllable deceleration and brake points.
    """
    
    segment_id: int
    target_speed_kmh: float  # Speed to achieve (corner entry)
    
    # Physics ceiling - CANNOT BE EXCEEDED
    max_deceleration_g: PhysicsCeiling = field(
        default_factory=lambda: PhysicsCeiling(1.5, "g", "tire_limit")
    )
    
    # Conservative deceleration
    conservative_decel_g: float = 0.8
    
    # Brake point
    brake_distance_m: float = 100.0  # Distance before corner
    
    # Safety buffer
    safety_distance_m: float = 10.0  # Extra stopping margin
    
    # Confidence
    confidence: Confidence = field(
        default_factory=lambda: Confidence(0.5, "braking", 0)
    )
    
    @staticmethod
    def compute_brake_distance(
        initial_speed_kmh: float,
        target_speed_kmh: float,
        deceleration_g: float,
        safety_margin_m: float = 10.0,
        reaction_time_s: float = 0.3
    ) -> float:
        """
        Compute required braking distance.
        
        Formula: d = (v1^2 - v2^2) / (2 * a) + reaction_distance + safety
        
        Args:
            initial_speed_kmh: Current/expected speed
            target_speed_kmh: Target speed
            deceleration_g: Deceleration in g
            safety_margin_m: Additional safety distance
            reaction_time_s: Driver reaction time
            
        Returns:
            Required braking distance in meters
        """
        if initial_speed_kmh <= target_speed_kmh:
            return 0.0
        
        # Convert to m/s
        v1 = initial_speed_kmh / 3.6
        v2 = target_speed_kmh / 3.6
        
        # Deceleration in m/s^2
        a = deceleration_g * 9.81
        
        # Physics braking distance
        d_brake = (v1**2 - v2**2) / (2 * a)
        
        # Reaction distance
        d_reaction = v1 * reaction_time_s
        
        # Total with safety
        return d_brake + d_reaction + safety_margin_m


@dataclass(frozen=True)
class SteeringEnvelope:
    """
    Steering intensity envelope.
    
    Defines maximum controllable steering rate and angle.
    """
    
    speed_kmh: float
    
    # Maximum steering rate based on speed
    max_steering_rate_deg_s: float = 90.0
    
    # Intensity threshold (fraction of max steering)
    normal_intensity: float = 0.5
    warning_intensity: float = 0.75
    limit_intensity: float = 0.9
    
    # Yaw rate expectations
    expected_yaw_rate_dps: float = 0.0
    yaw_rate_tolerance_dps: float = 5.0
    
    @staticmethod
    def get_max_steering_rate(speed_kmh: float) -> float:
        """
        Get maximum safe steering rate for speed.
        
        Higher speeds require slower steering inputs.
        """
        if speed_kmh < 50:
            return 180.0
        elif speed_kmh < 100:
            return 120.0
        elif speed_kmh < 150:
            return 90.0
        elif speed_kmh < 200:
            return 60.0
        else:
            return 45.0


@dataclass(frozen=True)
class CombinedGripEnvelope:
    """
    Combined grip (friction circle) envelope.
    
    Defines total available grip when combining braking/acceleration
    with cornering.
    """
    
    # Maximum grip (normalized to 1.0)
    max_total_grip: PhysicsCeiling = field(
        default_factory=lambda: PhysicsCeiling(1.0, "normalized", "friction_circle")
    )
    
    # Current usage
    longitudinal_grip_used: float = 0.0  # Braking/acceleration
    lateral_grip_used: float = 0.0        # Cornering
    
    # Stability margin
    stability_margin: float = 0.15  # 15% grip in reserve
    
    @property
    def total_grip_used(self) -> float:
        """Total grip used (friction circle)."""
        return math.sqrt(
            self.longitudinal_grip_used**2 +
            self.lateral_grip_used**2
        )
    
    @property
    def grip_remaining(self) -> float:
        """Available grip before limit."""
        return max(0.0, self.max_total_grip.value - self.total_grip_used)
    
    @property
    def is_at_limit(self) -> bool:
        """Check if at grip limit."""
        return self.grip_remaining < self.stability_margin
    
    @property
    def margin_fraction(self) -> float:
        """Fraction of grip in reserve."""
        return self.grip_remaining / self.max_total_grip.value


@dataclass
class SegmentEnvelope:
    """
    Complete envelope for a track segment.
    
    Combines all envelope types for comprehensive limits.
    """
    
    segment_id: int
    distance_start_m: float
    distance_end_m: float
    
    # Individual envelopes
    corner_speed: Optional[CornerSpeedEnvelope] = None
    braking: Optional[BrakingEnvelope] = None
    steering: Optional[SteeringEnvelope] = None
    combined_grip: Optional[CombinedGripEnvelope] = None
    
    # Overall confidence
    confidence: Confidence = field(
        default_factory=lambda: Confidence(0.5, "segment_envelope", 0)
    )
    
    @property
    def envelope_speed_kmh(self) -> float:
        """Get speed limit for this segment."""
        if self.corner_speed:
            return self.corner_speed.envelope_speed_kmh
        return 300.0  # Default maximum


@dataclass
class EnvelopeViolation:
    """
    Detected violation of a physics envelope.
    """
    
    timestamp_ms: int
    segment_id: int
    
    violation_type: EnvelopeType
    
    # Measured value
    measured_value: float
    measured_unit: str
    
    # Envelope limit
    envelope_limit: float
    
    # Severity
    excess_fraction: float  # How much over limit (0-1+)
    
    @property
    def severity(self) -> str:
        """Get severity level."""
        if self.excess_fraction < 0.05:
            return "minor"
        elif self.excess_fraction < 0.15:
            return "moderate"
        else:
            return "severe"


@dataclass
class EnvelopeComparison:
    """
    Comparison of actual performance to envelope.
    
    Used for post-lap analysis and learning.
    """
    
    segment_id: int
    
    # Speed comparison
    envelope_speed_kmh: float
    actual_speed_kmh: float
    speed_margin_kmh: float  # Positive = under envelope
    
    # Braking comparison
    envelope_brake_point_m: float
    actual_brake_point_m: float
    brake_margin_m: float  # Positive = braked earlier
    
    # Grip usage
    peak_grip_usage: float  # 0-1
    average_grip_usage: float
    
    # Assessment
    within_envelope: bool = True
    learning_candidate: bool = False  # Clean enough to learn from
