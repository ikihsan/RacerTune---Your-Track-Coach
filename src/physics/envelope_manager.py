"""
Envelope Manager
Safety-Critical Adaptive AI Race Coaching System

Manages physics envelopes for entire track and provides real-time lookup.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict

from ..types.geometry import TrackModel, TrackSegment
from ..types.envelopes import SegmentEnvelope, CornerSpeedEnvelope
from ..types.confidence import Confidence
from .corner_speed import CornerSpeedCalculator, CornerSpeedConfig
from .braking_envelope import BrakingCalculator, BrakingConfig
from .combined_grip import FrictionCircleEnforcer, FrictionCircleConfig


@dataclass
class EnvelopeManagerConfig:
    """Configuration for envelope manager."""
    
    corner_speed: CornerSpeedConfig = field(default_factory=CornerSpeedConfig)
    braking: BrakingConfig = field(default_factory=BrakingConfig)
    friction_circle: FrictionCircleConfig = field(default_factory=FrictionCircleConfig)
    
    # Lookahead for brake point calculation
    brake_lookahead_m: float = 500.0
    
    # Minimum envelope confidence for use
    min_envelope_confidence: float = 0.5


class EnvelopeManager:
    """
    Manages all physics envelopes for a track.
    
    Provides:
    - Pre-computed envelopes for each segment
    - Real-time envelope lookup by distance
    - Brake point calculation
    - Combined grip monitoring
    
    SAFETY:
    - Envelopes are computed conservatively
    - Low confidence = more conservative
    - Physics ceilings are never exceeded
    """
    
    def __init__(self, config: Optional[EnvelopeManagerConfig] = None):
        self.config = config or EnvelopeManagerConfig()
        
        self.corner_speed_calc = CornerSpeedCalculator(self.config.corner_speed)
        self.braking_calc = BrakingCalculator(self.config.braking)
        self.friction_circle = FrictionCircleEnforcer(self.config.friction_circle)
        
        # Cached envelopes
        self._segment_envelopes: Dict[int, SegmentEnvelope] = {}
        self._track_length_m: float = 0.0
    
    def build_envelopes(self, track: TrackModel) -> None:
        """
        Build all physics envelopes for a track.
        
        Args:
            track: Track model with segments
        """
        self._segment_envelopes.clear()
        self._track_length_m = track.total_length_m
        
        for segment in track.segments:
            envelope = self._build_segment_envelope(segment, track)
            self._segment_envelopes[segment.segment_id] = envelope
    
    def _build_segment_envelope(
        self,
        segment: TrackSegment,
        track: TrackModel
    ) -> SegmentEnvelope:
        """Build envelope for a single segment."""
        
        # Corner speed envelope
        corner_speed = self.corner_speed_calc.compute_for_segment(segment)
        
        # Find next corner for brake point calculation
        next_corner = self._find_next_corner(segment, track)
        
        braking = None
        if next_corner and segment.is_corner is False:
            # Compute brake point for approaching corner
            _, braking = self.braking_calc.compute_brake_point(
                current_speed_kmh=200.0,  # Assume high approach speed
                target_speed_kmh=corner_speed.envelope_speed_kmh,
                corner_entry_distance_m=next_corner.start_distance_m - segment.end_distance_m
            )
        
        return SegmentEnvelope(
            segment_id=segment.segment_id,
            distance_start_m=segment.start_distance_m,
            distance_end_m=segment.end_distance_m,
            corner_speed=corner_speed,
            braking=braking,
            confidence=Confidence(
                value=segment.geometry_confidence,
                source="envelope",
                timestamp_ms=0
            )
        )
    
    def _find_next_corner(
        self,
        current_segment: TrackSegment,
        track: TrackModel
    ) -> Optional[TrackSegment]:
        """Find the next corner segment after current."""
        
        for segment in track.segments:
            if segment.start_distance_m > current_segment.end_distance_m:
                if segment.is_corner:
                    return segment
        
        # Wrap around to start of track
        for segment in track.segments:
            if segment.is_corner:
                return segment
        
        return None
    
    def get_envelope_at_distance(self, distance_m: float) -> Optional[SegmentEnvelope]:
        """
        Get envelope at a specific track distance.
        
        Args:
            distance_m: Distance from start/finish
            
        Returns:
            Segment envelope, or None if not available
        """
        # Wrap distance
        if self._track_length_m > 0:
            distance_m = distance_m % self._track_length_m
        
        for envelope in self._segment_envelopes.values():
            if envelope.distance_start_m <= distance_m < envelope.distance_end_m:
                return envelope
        
        return None
    
    def get_speed_limit_at_distance(self, distance_m: float) -> float:
        """
        Get speed limit at a specific distance.
        
        Args:
            distance_m: Distance from start/finish
            
        Returns:
            Speed limit in km/h
        """
        envelope = self.get_envelope_at_distance(distance_m)
        
        if envelope and envelope.corner_speed:
            return envelope.corner_speed.envelope_speed_kmh
        
        return 300.0  # Default max
    
    def get_speed_envelope_ahead(
        self,
        current_distance_m: float,
        lookahead_m: float
    ) -> List[tuple]:
        """
        Get speed envelope for track ahead.
        
        Returns:
            List of (distance_ahead, speed_limit) tuples
        """
        result = []
        
        distance = current_distance_m
        end_distance = current_distance_m + lookahead_m
        
        while distance < end_distance:
            speed_limit = self.get_speed_limit_at_distance(distance)
            result.append((distance - current_distance_m, speed_limit))
            distance += 10.0  # 10m resolution
        
        return result
    
    def check_speed_at_distance(
        self,
        distance_m: float,
        current_speed_kmh: float
    ) -> tuple:
        """
        Check if current speed is within envelope.
        
        Returns:
            Tuple of (is_within_envelope, margin_kmh, envelope_speed_kmh)
        """
        envelope_speed = self.get_speed_limit_at_distance(distance_m)
        margin = envelope_speed - current_speed_kmh
        is_within = margin >= 0
        
        return is_within, margin, envelope_speed
    
    def compute_brake_advisory(
        self,
        current_distance_m: float,
        current_speed_kmh: float
    ) -> Optional[dict]:
        """
        Compute braking advisory for upcoming corners.
        
        Returns:
            Advisory dict or None if no braking needed
        """
        # Look ahead for corners
        lookahead = self.config.brake_lookahead_m
        
        envelope_ahead = self.get_speed_envelope_ahead(current_distance_m, lookahead)
        
        for distance_ahead, speed_limit in envelope_ahead:
            if speed_limit < current_speed_kmh:
                # Need to slow down for this point
                is_late, margin = self.braking_calc.is_braking_late(
                    current_speed_kmh,
                    speed_limit,
                    distance_ahead
                )
                
                brake_point, envelope = self.braking_calc.compute_brake_point(
                    current_speed_kmh,
                    speed_limit,
                    distance_ahead
                )
                
                return {
                    "distance_to_corner_m": distance_ahead,
                    "target_speed_kmh": speed_limit,
                    "brake_point_m": brake_point,
                    "is_late": is_late,
                    "margin_m": margin,
                    "required_decel_g": envelope.conservative_decel_g
                }
        
        return None
    
    def update_from_learning(
        self,
        segment_id: int,
        learned_speed_kmh: float,
        blend_weight: float
    ) -> bool:
        """
        Update envelope with learned data.
        
        SAFETY: Learned values are clamped to physics ceiling.
        
        Returns:
            True if update was applied
        """
        if segment_id not in self._segment_envelopes:
            return False
        
        envelope = self._segment_envelopes[segment_id]
        
        if not envelope.corner_speed:
            return False
        
        # Apply learning with blend
        new_corner_speed = envelope.corner_speed.blend_with_learned(
            learned_speed_kmh,
            blend_weight
        )
        
        # Create new envelope with updated corner speed
        self._segment_envelopes[segment_id] = SegmentEnvelope(
            segment_id=envelope.segment_id,
            distance_start_m=envelope.distance_start_m,
            distance_end_m=envelope.distance_end_m,
            corner_speed=new_corner_speed,
            braking=envelope.braking,
            steering=envelope.steering,
            combined_grip=envelope.combined_grip,
            confidence=envelope.confidence
        )
        
        return True
    
    def get_all_envelopes(self) -> List[SegmentEnvelope]:
        """Get all segment envelopes."""
        return list(self._segment_envelopes.values())
    
    def reset(self) -> None:
        """Clear all envelopes."""
        self._segment_envelopes.clear()
        self._track_length_m = 0.0
