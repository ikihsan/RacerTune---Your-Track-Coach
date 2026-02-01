"""
Corner Speed Calculator
Safety-Critical Adaptive AI Race Coaching System

Computes maximum controllable corner speeds based on physics.

SAFETY INVARIANT S2: Physics envelopes are HARD CEILINGS.
"""

from dataclasses import dataclass
from typing import Optional
import math

from ..types.geometry import TrackSegment, TrackPoint
from ..types.envelopes import CornerSpeedEnvelope, PhysicsCeiling
from ..types.confidence import Confidence


@dataclass
class CornerSpeedConfig:
    """Configuration for corner speed calculation."""
    
    # Tire parameters
    tire_friction_mu: float = 1.0  # Coefficient of friction
    
    # Safety margins
    safety_factor: float = 0.85  # 15% safety margin
    low_confidence_penalty: float = 0.85  # Additional 15% at low confidence
    
    # Limits
    absolute_max_speed_kmh: float = 300.0
    absolute_min_speed_kmh: float = 20.0
    
    # Confidence thresholds
    high_confidence_threshold: float = 0.9
    low_confidence_threshold: float = 0.7


class CornerSpeedCalculator:
    """
    Calculates maximum controllable corner speed.
    
    Based on the fundamental physics equation:
    v = sqrt(g * mu * r)
    
    Where:
    - v = velocity (m/s)
    - g = gravitational acceleration (9.81 m/s²)
    - mu = tire friction coefficient
    - r = corner radius (m)
    
    SAFETY:
    - This is NOT the maximum possible speed
    - This is the maximum CONTROLLABLE speed
    - Safety margins are always applied
    - Lower confidence = more conservative
    """
    
    GRAVITY = 9.81  # m/s²
    
    def __init__(self, config: Optional[CornerSpeedConfig] = None):
        self.config = config or CornerSpeedConfig()
    
    def compute_for_segment(
        self,
        segment: TrackSegment
    ) -> CornerSpeedEnvelope:
        """
        Compute corner speed envelope for a track segment.
        
        Args:
            segment: Track segment with curvature data
            
        Returns:
            Corner speed envelope for the segment
        """
        # Get minimum radius in segment (tightest point)
        min_radius = segment.minimum_radius_m
        
        # Compute physics ceiling (absolute maximum)
        physics_max_m_s = self._compute_physics_limit(
            min_radius,
            self.config.tire_friction_mu
        )
        
        physics_max_kmh = physics_max_m_s * 3.6
        
        # Clamp to absolute limits
        physics_max_kmh = min(physics_max_kmh, self.config.absolute_max_speed_kmh)
        physics_max_kmh = max(physics_max_kmh, self.config.absolute_min_speed_kmh)
        
        # Create physics ceiling
        physics_ceiling = PhysicsCeiling(
            value=physics_max_kmh,
            unit="km/h",
            source="friction_limit"
        )
        
        # Apply safety factor for conservative estimate
        conservative_kmh = physics_max_kmh * self.config.safety_factor
        
        # Apply additional penalty for low confidence geometry
        if segment.geometry_confidence < self.config.low_confidence_threshold:
            conservative_kmh *= self.config.low_confidence_penalty
        
        # Create confidence
        confidence = Confidence(
            value=segment.geometry_confidence,
            source="corner_speed",
            timestamp_ms=0,
            degradation_reason=None if segment.geometry_confidence > 0.8 else "low_geometry_confidence"
        )
        
        return CornerSpeedEnvelope(
            segment_id=segment.segment_id,
            distance_start_m=segment.start_distance_m,
            distance_end_m=segment.end_distance_m,
            physics_ceiling_kmh=physics_ceiling,
            conservative_speed_kmh=conservative_kmh,
            envelope_speed_kmh=conservative_kmh,  # Start with conservative
            corner_radius_m=min_radius,
            curvature_1_per_m=segment.average_curvature_1_per_m,
            confidence=confidence
        )
    
    def compute_for_point(
        self,
        point: TrackPoint
    ) -> float:
        """
        Compute speed limit at a single point.
        
        Args:
            point: Track point with curvature
            
        Returns:
            Speed limit in km/h
        """
        radius = point.radius_m
        
        if radius == float('inf') or radius > 10000:
            return self.config.absolute_max_speed_kmh
        
        physics_max_m_s = self._compute_physics_limit(
            radius,
            self.config.tire_friction_mu
        )
        
        physics_max_kmh = physics_max_m_s * 3.6
        
        # Apply safety factor
        safe_kmh = physics_max_kmh * self.config.safety_factor
        
        # Apply confidence penalty
        if point.curvature_confidence < self.config.low_confidence_threshold:
            safe_kmh *= self.config.low_confidence_penalty
        
        return min(safe_kmh, self.config.absolute_max_speed_kmh)
    
    def _compute_physics_limit(
        self,
        radius_m: float,
        friction_mu: float
    ) -> float:
        """
        Compute raw physics speed limit.
        
        v = sqrt(g * mu * r)
        """
        if radius_m <= 0:
            return 0.0
        
        if radius_m == float('inf'):
            return self.config.absolute_max_speed_kmh / 3.6
        
        v_m_s = math.sqrt(self.GRAVITY * friction_mu * radius_m)
        
        return v_m_s
    
    def compute_with_banking(
        self,
        radius_m: float,
        banking_deg: float,
        friction_mu: float
    ) -> float:
        """
        Compute speed limit with banked track.
        
        v = sqrt(r * g * (tan(theta) + mu) / (1 - mu * tan(theta)))
        
        Args:
            radius_m: Corner radius
            banking_deg: Track banking angle (positive = banked toward corner)
            friction_mu: Tire friction coefficient
            
        Returns:
            Speed limit in m/s
        """
        if radius_m <= 0 or radius_m == float('inf'):
            return self.config.absolute_max_speed_kmh / 3.6
        
        theta_rad = math.radians(banking_deg)
        tan_theta = math.tan(theta_rad)
        
        numerator = radius_m * self.GRAVITY * (tan_theta + friction_mu)
        denominator = 1 - friction_mu * tan_theta
        
        if denominator <= 0:
            # Banking angle too steep - theoretical infinite speed
            return self.config.absolute_max_speed_kmh / 3.6
        
        v_m_s = math.sqrt(numerator / denominator)
        
        return v_m_s
    
    def explain_limit(
        self,
        radius_m: float,
        speed_limit_kmh: float
    ) -> str:
        """
        Generate explanation for a speed limit.
        
        Used for post-lap analysis and driver understanding.
        """
        if radius_m == float('inf'):
            return "Straight section - no cornering limit"
        
        physics_max_m_s = self._compute_physics_limit(radius_m, self.config.tire_friction_mu)
        physics_max_kmh = physics_max_m_s * 3.6
        
        safety_margin = (1 - speed_limit_kmh / physics_max_kmh) * 100
        
        return (
            f"Corner radius: {radius_m:.0f}m\n"
            f"Physics limit: {physics_max_kmh:.0f} km/h\n"
            f"Controllable limit: {speed_limit_kmh:.0f} km/h\n"
            f"Safety margin: {safety_margin:.0f}%\n"
            f"Based on: friction μ = {self.config.tire_friction_mu:.2f}"
        )
