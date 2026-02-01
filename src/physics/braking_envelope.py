"""
Braking Envelope Calculator
Safety-Critical Adaptive AI Race Coaching System

Computes braking distances and deceleration limits.

SAFETY: Braking calculations include safety margins and reaction time.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import math

from ..types.envelopes import BrakingEnvelope, PhysicsCeiling
from ..types.confidence import Confidence


@dataclass
class BrakingConfig:
    """Configuration for braking calculations."""
    
    # Deceleration limits
    max_deceleration_g: float = 1.0  # Conservative road car
    braking_efficiency: float = 0.9  # Account for fade, imperfect technique
    
    # Human factors
    reaction_time_s: float = 0.3  # Time to move foot to brake
    
    # Safety margins
    safety_distance_m: float = 10.0  # Extra stopping distance
    safety_factor: float = 1.15  # 15% additional distance
    
    # Surface variability
    surface_factor: float = 0.95  # Account for variable grip
    
    # Limits
    min_braking_distance_m: float = 5.0
    max_braking_distance_m: float = 500.0


class BrakingCalculator:
    """
    Calculates braking distances and deceleration limits.
    
    Formula:
    d = v²/(2*a) + v*t_reaction + safety_margin
    
    Where:
    - d = stopping distance
    - v = initial velocity
    - a = deceleration
    - t_reaction = reaction time
    
    SAFETY:
    - Reaction time is always included
    - Safety margins are always applied
    - Deceleration is conservative, not maximum
    """
    
    GRAVITY = 9.81  # m/s²
    
    def __init__(self, config: Optional[BrakingConfig] = None):
        self.config = config or BrakingConfig()
    
    def compute_brake_point(
        self,
        current_speed_kmh: float,
        target_speed_kmh: float,
        corner_entry_distance_m: float
    ) -> Tuple[float, BrakingEnvelope]:
        """
        Compute brake point for a corner.
        
        Args:
            current_speed_kmh: Expected approach speed
            target_speed_kmh: Required corner entry speed
            corner_entry_distance_m: Distance to corner entry
            
        Returns:
            Tuple of (brake point distance from now, envelope)
        """
        if current_speed_kmh <= target_speed_kmh:
            # No braking needed
            envelope = BrakingEnvelope(
                segment_id=0,
                target_speed_kmh=target_speed_kmh,
                max_deceleration_g=PhysicsCeiling(
                    value=self.config.max_deceleration_g,
                    unit="g",
                    source="braking_limit"
                ),
                conservative_decel_g=0.0,
                brake_distance_m=0.0,
                safety_distance_m=0.0
            )
            return corner_entry_distance_m, envelope
        
        # Compute required braking distance
        brake_distance = self._compute_stopping_distance(
            current_speed_kmh,
            target_speed_kmh
        )
        
        # Compute brake point (distance before corner entry)
        brake_point = corner_entry_distance_m - brake_distance
        
        # Ensure brake point is positive (in front of us)
        brake_point = max(0.0, brake_point)
        
        # Compute actual deceleration needed
        decel_g = self._compute_required_deceleration(
            current_speed_kmh,
            target_speed_kmh,
            brake_distance
        )
        
        envelope = BrakingEnvelope(
            segment_id=0,
            target_speed_kmh=target_speed_kmh,
            max_deceleration_g=PhysicsCeiling(
                value=self.config.max_deceleration_g,
                unit="g",
                source="braking_limit"
            ),
            conservative_decel_g=decel_g,
            brake_distance_m=brake_distance,
            safety_distance_m=self.config.safety_distance_m,
            confidence=Confidence(
                value=0.8,
                source="braking",
                timestamp_ms=0
            )
        )
        
        return brake_point, envelope
    
    def _compute_stopping_distance(
        self,
        initial_speed_kmh: float,
        final_speed_kmh: float
    ) -> float:
        """
        Compute required stopping distance.
        
        Includes reaction distance and safety margin.
        """
        # Convert to m/s
        v1 = initial_speed_kmh / 3.6
        v2 = final_speed_kmh / 3.6
        
        if v1 <= v2:
            return 0.0
        
        # Effective deceleration
        a = (
            self.config.max_deceleration_g *
            self.GRAVITY *
            self.config.braking_efficiency *
            self.config.surface_factor
        )
        
        # Physics braking distance: d = (v1² - v2²) / (2*a)
        d_physics = (v1**2 - v2**2) / (2 * a)
        
        # Reaction distance: d_reaction = v1 * t_reaction
        d_reaction = v1 * self.config.reaction_time_s
        
        # Total with safety factor
        d_total = (d_physics + d_reaction) * self.config.safety_factor
        
        # Add fixed safety margin
        d_total += self.config.safety_distance_m
        
        # Clamp to limits
        d_total = max(self.config.min_braking_distance_m, d_total)
        d_total = min(self.config.max_braking_distance_m, d_total)
        
        return d_total
    
    def _compute_required_deceleration(
        self,
        initial_speed_kmh: float,
        final_speed_kmh: float,
        distance_m: float
    ) -> float:
        """
        Compute deceleration needed to stop in given distance.
        
        Returns deceleration in g.
        """
        if distance_m <= 0:
            return self.config.max_deceleration_g
        
        # Convert to m/s
        v1 = initial_speed_kmh / 3.6
        v2 = final_speed_kmh / 3.6
        
        if v1 <= v2:
            return 0.0
        
        # Subtract reaction distance
        reaction_distance = v1 * self.config.reaction_time_s
        braking_distance = distance_m - reaction_distance - self.config.safety_distance_m
        
        if braking_distance <= 0:
            return self.config.max_deceleration_g  # Emergency braking
        
        # a = (v1² - v2²) / (2*d)
        a_m_s2 = (v1**2 - v2**2) / (2 * braking_distance)
        a_g = a_m_s2 / self.GRAVITY
        
        # Clamp to maximum
        return min(a_g, self.config.max_deceleration_g)
    
    def is_braking_late(
        self,
        current_speed_kmh: float,
        target_speed_kmh: float,
        distance_to_corner_m: float
    ) -> Tuple[bool, float]:
        """
        Check if braking is late for the upcoming corner.
        
        Args:
            current_speed_kmh: Current speed
            target_speed_kmh: Required corner speed
            distance_to_corner_m: Distance to corner entry
            
        Returns:
            Tuple of (is_late, margin_m)
            margin_m is positive if on time, negative if late
        """
        required_distance = self._compute_stopping_distance(
            current_speed_kmh,
            target_speed_kmh
        )
        
        margin = distance_to_corner_m - required_distance
        is_late = margin < 0
        
        return is_late, margin
    
    def compute_trail_braking_profile(
        self,
        entry_speed_kmh: float,
        apex_speed_kmh: float,
        distance_to_apex_m: float
    ) -> list:
        """
        Compute a trail braking deceleration profile.
        
        Trail braking: decreasing braking force as steering increases.
        
        Returns list of (distance_fraction, decel_fraction) tuples.
        """
        # Simplified linear trail-off
        # In reality this would be more complex
        
        profile = [
            (0.0, 1.0),    # Full braking at entry
            (0.3, 0.8),    # 80% at 30% through
            (0.5, 0.5),    # 50% at midpoint
            (0.7, 0.2),    # 20% approaching apex
            (1.0, 0.0),    # No braking at apex
        ]
        
        return profile
    
    def explain_brake_point(
        self,
        current_speed_kmh: float,
        target_speed_kmh: float,
        brake_point_m: float,
        corner_entry_m: float
    ) -> str:
        """Generate explanation for brake point calculation."""
        
        speed_reduction = current_speed_kmh - target_speed_kmh
        braking_distance = corner_entry_m - brake_point_m
        
        decel_g = self._compute_required_deceleration(
            current_speed_kmh, target_speed_kmh, braking_distance
        )
        
        return (
            f"Speed reduction: {current_speed_kmh:.0f} → {target_speed_kmh:.0f} km/h "
            f"(-{speed_reduction:.0f} km/h)\n"
            f"Braking distance: {braking_distance:.0f}m\n"
            f"Required deceleration: {decel_g:.2f}g\n"
            f"Reaction time allowance: {self.config.reaction_time_s:.1f}s\n"
            f"Safety margin: {self.config.safety_distance_m:.0f}m"
        )
