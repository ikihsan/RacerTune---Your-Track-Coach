"""
Blend Engine
Safety-Critical Adaptive AI Race Coaching System

Blends learned behavior with physics-based envelopes.

SAFETY INVARIANT S4: Physics models are hard ceilings.
Learning may only reduce conservatism, NEVER exceed physics.
"""

from dataclasses import dataclass
from typing import Optional

from ..types.envelopes import (
    PhysicsCeiling,
    CornerSpeedEnvelope,
    BrakingEnvelope
)
from .segment_stats import SegmentStatistics


@dataclass
class BlendConfig:
    """Configuration for envelope blending."""
    
    # Maximum influence from learned data
    # This is a HARD LIMIT - learned data can never have more than this influence
    max_learned_influence: float = 0.30  # 30% max
    
    # Minimum observations needed for any learning influence
    min_observations_for_learning: int = 3
    
    # Observations for maximum influence
    observations_for_full_influence: int = 20
    
    # Safety margin on learned values
    learned_safety_margin: float = 0.05  # 5% additional safety on learned


@dataclass
class BlendResult:
    """Result of blending physics with learned data."""
    
    # Blended value
    blended_value: float
    
    # Physics ceiling (for reference)
    physics_ceiling: float
    
    # Learned contribution (if any)
    learned_value: Optional[float] = None
    learned_weight: float = 0.0
    
    # Metadata
    observation_count: int = 0
    was_physics_limited: bool = False  # True if learned exceeded physics


class BlendEngine:
    """
    Blends learned behavior with physics-based envelopes.
    
    This is the critical safety component that ensures learning
    can only REDUCE conservatism, never exceed physics limits.
    
    SAFETY INVARIANT S4: Physics models are hard ceilings.
    
    The blend formula is:
    
    blended = physics_ceiling - (physics_ceiling - learned) * learned_weight
    
    Where:
    - physics_ceiling is the MAXIMUM safe value from physics model
    - learned is the observed safe value from driver data
    - learned_weight is capped at max_learned_influence
    
    This ensures:
    1. blended <= physics_ceiling (always)
    2. If learned > physics_ceiling, it's ignored (physics wins)
    3. Learning can only move values toward learned (more relaxed)
    4. Physics ceiling is always the hard limit
    """
    
    def __init__(self, config: Optional[BlendConfig] = None):
        self.config = config or BlendConfig()
    
    def blend_corner_speed(
        self,
        physics_envelope: CornerSpeedEnvelope,
        segment_stats: Optional[SegmentStatistics]
    ) -> BlendResult:
        """
        Blend physics corner speed with learned data.
        
        Args:
            physics_envelope: Physics-based speed envelope
            segment_stats: Learned statistics (may be None)
            
        Returns:
            BlendResult with blended speed
        """
        physics_ceiling = physics_envelope.max_speed_kmh
        
        # No learning data: use physics
        if segment_stats is None or not segment_stats.has_sufficient_data:
            return BlendResult(
                blended_value=physics_ceiling,
                physics_ceiling=physics_ceiling,
                learned_value=None,
                learned_weight=0.0,
                observation_count=segment_stats.observation_count if segment_stats else 0
            )
        
        # Get learned value (already capped at physics ceiling internally)
        learned_speed = segment_stats.get_learned_entry_speed(physics_ceiling)
        
        # Compute blend weight
        learned_weight = self._compute_learned_weight(segment_stats)
        
        # SAFETY CHECK: Learned must not exceed physics
        if learned_speed > physics_ceiling:
            # This should never happen due to capping, but defense in depth
            return BlendResult(
                blended_value=physics_ceiling,
                physics_ceiling=physics_ceiling,
                learned_value=learned_speed,
                learned_weight=0.0,  # Ignore learned
                observation_count=segment_stats.observation_count,
                was_physics_limited=True
            )
        
        # Apply blend: physics dominates, learning can only reduce conservatism
        # But since learned <= physics, and we want to move toward learned,
        # the blended value will be between learned and physics
        blended = physics_ceiling - (physics_ceiling - learned_speed) * learned_weight
        
        # Apply additional safety margin on learned contribution
        safety_reduction = (physics_ceiling - blended) * self.config.learned_safety_margin
        blended -= safety_reduction
        
        return BlendResult(
            blended_value=blended,
            physics_ceiling=physics_ceiling,
            learned_value=learned_speed,
            learned_weight=learned_weight,
            observation_count=segment_stats.observation_count
        )
    
    def blend_brake_point(
        self,
        physics_envelope: BrakingEnvelope,
        segment_stats: Optional[SegmentStatistics]
    ) -> BlendResult:
        """
        Blend physics brake point with learned data.
        
        For braking, LARGER distance = EARLIER = SAFER.
        Learning can only allow LATER braking (smaller distance),
        but never later than physics allows.
        
        Args:
            physics_envelope: Physics-based braking envelope
            segment_stats: Learned statistics (may be None)
            
        Returns:
            BlendResult with blended brake point distance
        """
        physics_minimum = physics_envelope.minimum_brake_distance_m
        
        # No learning data: use physics (conservative/early)
        if segment_stats is None or not segment_stats.has_sufficient_data:
            return BlendResult(
                blended_value=physics_minimum,
                physics_ceiling=physics_minimum,
                learned_value=None,
                learned_weight=0.0,
                observation_count=segment_stats.observation_count if segment_stats else 0
            )
        
        # Get learned brake point
        learned_point = segment_stats.get_learned_brake_point(physics_minimum)
        
        # Compute blend weight
        learned_weight = self._compute_learned_weight(segment_stats)
        
        # SAFETY CHECK: Learned must not be later than physics
        # (smaller distance = later = less safe)
        if learned_point < physics_minimum:
            return BlendResult(
                blended_value=physics_minimum,
                physics_ceiling=physics_minimum,
                learned_value=learned_point,
                learned_weight=0.0,
                observation_count=segment_stats.observation_count,
                was_physics_limited=True
            )
        
        # Blend: allow braking slightly later based on learned data
        # physics_minimum is the latest safe point
        # learned_point is earlier (larger) or equal
        # We can move from learned toward physics (later) based on weight
        blended = learned_point - (learned_point - physics_minimum) * learned_weight
        
        # Apply safety margin (brake earlier)
        safety_addition = (learned_point - blended) * self.config.learned_safety_margin
        blended += safety_addition
        
        return BlendResult(
            blended_value=blended,
            physics_ceiling=physics_minimum,
            learned_value=learned_point,
            learned_weight=learned_weight,
            observation_count=segment_stats.observation_count
        )
    
    def _compute_learned_weight(self, stats: SegmentStatistics) -> float:
        """
        Compute weight for learned data.
        
        Weight scales with observation count, capped at max_learned_influence.
        """
        effective_count = stats.effective_observation_count
        
        if effective_count < self.config.min_observations_for_learning:
            return 0.0
        
        # Linear ramp from min to full observations
        ramp_range = self.config.observations_for_full_influence - self.config.min_observations_for_learning
        
        if ramp_range <= 0:
            weight = 1.0
        else:
            progress = (effective_count - self.config.min_observations_for_learning) / ramp_range
            weight = min(progress, 1.0)
        
        # Apply maximum influence cap
        return weight * self.config.max_learned_influence
    
    def get_max_allowed_influence(self) -> float:
        """Get the maximum allowed learned influence."""
        return self.config.max_learned_influence
