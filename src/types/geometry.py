"""
Track Geometry Types
Safety-Critical Adaptive AI Race Coaching System

This module defines all track geometry data structures.

SAFETY INVARIANT: Track geometry confidence must propagate to envelope computation.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Tuple
import math

from .confidence import Confidence


class CornerDirection(Enum):
    """Direction of a corner."""
    LEFT = auto()
    RIGHT = auto()
    STRAIGHT = auto()


class CornerPhase(Enum):
    """
    Phase of corner traversal.
    
    Used for voice arbitration - determines when speech is allowed.
    """
    STRAIGHT = auto()      # On straight, no corner imminent
    APPROACH = auto()      # 50-200m before corner entry
    ENTRY = auto()         # Turn-in to apex
    APEX = auto()          # At or near apex - VOICE FORBIDDEN
    EXIT = auto()          # Apex to track-out
    
    @property
    def allows_voice(self) -> bool:
        """Check if voice output is permitted in this phase."""
        return self != CornerPhase.APEX
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a high-workload phase."""
        return self in [CornerPhase.ENTRY, CornerPhase.APEX]


@dataclass(frozen=True)
class TrackPoint:
    """
    Single point on track centerline with metadata.
    """
    
    # Position (WGS84)
    latitude_deg: float
    longitude_deg: float
    altitude_m: Optional[float] = None
    
    # Track progress
    distance_m: float = 0.0  # Distance from start/finish
    
    # Local geometry
    curvature_1_per_m: float = 0.0  # 1/radius, positive = left turn
    heading_deg: float = 0.0  # Track heading at this point
    gradient_percent: float = 0.0  # Positive = uphill
    
    # Track width (if available)
    track_width_m: Optional[float] = None
    
    # Confidence
    position_confidence: float = 0.5
    curvature_confidence: float = 0.5
    
    @property
    def radius_m(self) -> float:
        """Corner radius in meters. Returns infinity for straights."""
        if abs(self.curvature_1_per_m) < 1e-6:
            return float('inf')
        return 1.0 / abs(self.curvature_1_per_m)
    
    @property
    def direction(self) -> CornerDirection:
        """Get corner direction from curvature."""
        if abs(self.curvature_1_per_m) < 0.001:  # ~1000m radius threshold
            return CornerDirection.STRAIGHT
        elif self.curvature_1_per_m > 0:
            return CornerDirection.LEFT
        else:
            return CornerDirection.RIGHT
    
    @property
    def overall_confidence(self) -> float:
        """Combined confidence for this point."""
        return min(self.position_confidence, self.curvature_confidence)


@dataclass
class TrackSegment:
    """
    A segment of track with consistent characteristics.
    
    Segments are the unit of adaptive learning.
    """
    
    segment_id: int
    start_distance_m: float
    end_distance_m: float
    
    # Segment type
    is_corner: bool = False
    direction: CornerDirection = CornerDirection.STRAIGHT
    corner_name: Optional[str] = None  # e.g., "Turn 1", "Hairpin"
    
    # Geometry (representative values)
    average_curvature_1_per_m: float = 0.0
    minimum_radius_m: float = float('inf')
    average_heading_deg: float = 0.0
    heading_change_deg: float = 0.0  # Total heading change through segment
    
    # Track width
    average_width_m: Optional[float] = None
    minimum_width_m: Optional[float] = None
    
    # Points in this segment
    points: List[TrackPoint] = field(default_factory=list)
    
    # Confidence
    geometry_confidence: float = 0.5
    
    @property
    def length_m(self) -> float:
        """Segment length in meters."""
        return self.end_distance_m - self.start_distance_m
    
    @property
    def midpoint_distance_m(self) -> float:
        """Distance to segment midpoint."""
        return (self.start_distance_m + self.end_distance_m) / 2
    
    def contains_distance(self, distance_m: float) -> bool:
        """Check if a distance falls within this segment."""
        return self.start_distance_m <= distance_m < self.end_distance_m


@dataclass
class TrackModel:
    """
    Complete track model with centerline and segments.
    
    This is the core data structure for track geometry.
    """
    
    track_id: str
    track_name: str
    
    # Track metadata
    total_length_m: float = 0.0
    creation_timestamp_ms: int = 0
    last_update_ms: int = 0
    
    # Data sources used
    gps_laps_used: int = 0
    satellite_reference_used: bool = False
    imu_fusion_used: bool = False
    edge_detection_used: bool = False
    
    # Centerline
    centerline: List[TrackPoint] = field(default_factory=list)
    
    # Segments
    segments: List[TrackSegment] = field(default_factory=list)
    
    # Start/finish line
    start_finish_distance_m: float = 0.0
    start_finish_latitude_deg: float = 0.0
    start_finish_longitude_deg: float = 0.0
    start_finish_heading_deg: float = 0.0
    
    # Overall confidence
    geometry_confidence: Confidence = field(
        default_factory=lambda: Confidence(0.0, "track", 0)
    )
    
    @property
    def is_valid(self) -> bool:
        """Check if track model is valid for use."""
        return (
            len(self.centerline) >= 10 and
            len(self.segments) >= 1 and
            self.total_length_m >= 500 and
            self.geometry_confidence.value >= 0.5
        )
    
    @property
    def corner_count(self) -> int:
        """Number of corner segments."""
        return sum(1 for s in self.segments if s.is_corner)
    
    def get_segment_at_distance(self, distance_m: float) -> Optional[TrackSegment]:
        """Get segment containing the given distance."""
        # Wrap distance to track length
        wrapped_distance = distance_m % self.total_length_m
        
        for segment in self.segments:
            if segment.contains_distance(wrapped_distance):
                return segment
        
        return None
    
    def get_point_at_distance(self, distance_m: float) -> Optional[TrackPoint]:
        """Get interpolated point at given distance."""
        if not self.centerline:
            return None
        
        # Wrap distance
        wrapped_distance = distance_m % self.total_length_m
        
        # Find surrounding points
        for i in range(len(self.centerline) - 1):
            p1 = self.centerline[i]
            p2 = self.centerline[i + 1]
            
            if p1.distance_m <= wrapped_distance < p2.distance_m:
                # Linear interpolation
                t = (wrapped_distance - p1.distance_m) / (p2.distance_m - p1.distance_m)
                
                return TrackPoint(
                    latitude_deg=p1.latitude_deg + t * (p2.latitude_deg - p1.latitude_deg),
                    longitude_deg=p1.longitude_deg + t * (p2.longitude_deg - p1.longitude_deg),
                    altitude_m=p1.altitude_m if p1.altitude_m else None,
                    distance_m=wrapped_distance,
                    curvature_1_per_m=p1.curvature_1_per_m + t * (p2.curvature_1_per_m - p1.curvature_1_per_m),
                    heading_deg=p1.heading_deg + t * (p2.heading_deg - p1.heading_deg),
                    position_confidence=min(p1.position_confidence, p2.position_confidence),
                    curvature_confidence=min(p1.curvature_confidence, p2.curvature_confidence)
                )
        
        return None
    
    def get_curvature_ahead(
        self,
        current_distance_m: float,
        lookahead_m: float
    ) -> List[Tuple[float, float]]:
        """
        Get curvature profile ahead of current position.
        
        Returns:
            List of (distance, curvature) tuples
        """
        result = []
        
        for point in self.centerline:
            # Calculate distance ahead (handling wrap-around)
            delta = (point.distance_m - current_distance_m) % self.total_length_m
            
            if delta <= lookahead_m:
                result.append((delta, point.curvature_1_per_m))
        
        result.sort(key=lambda x: x[0])
        return result


@dataclass
class CornerApex:
    """
    Identified apex point of a corner.
    """
    
    segment_id: int
    apex_distance_m: float
    apex_curvature_1_per_m: float
    
    # Geometry
    corner_direction: CornerDirection = CornerDirection.STRAIGHT
    minimum_radius_m: float = float('inf')
    
    # Entry/exit distances
    entry_distance_m: float = 0.0
    exit_distance_m: float = 0.0
    
    # Optimal speed (from physics envelope)
    envelope_speed_kmh: Optional[float] = None
    
    # Confidence
    confidence: float = 0.5


@dataclass
class TrackPosition:
    """
    Current position on track relative to track model.
    """
    
    timestamp_ms: int
    
    # Position on track
    distance_m: float
    lateral_offset_m: float = 0.0  # Offset from centerline (+ = right)
    
    # Current segment
    segment_id: int = 0
    corner_phase: CornerPhase = CornerPhase.STRAIGHT
    
    # Distance to next features
    distance_to_next_corner_m: float = float('inf')
    distance_to_apex_m: float = float('inf')
    distance_to_corner_exit_m: float = float('inf')
    
    # Confidence
    position_confidence: float = 0.5
    
    @property
    def in_corner(self) -> bool:
        """Check if currently in a corner."""
        return self.corner_phase in [
            CornerPhase.ENTRY,
            CornerPhase.APEX,
            CornerPhase.EXIT
        ]
    
    @property
    def at_apex(self) -> bool:
        """Check if at or near apex."""
        return self.corner_phase == CornerPhase.APEX
