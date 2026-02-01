"""
Track Geometry Builder
Safety-Critical Adaptive AI Race Coaching System

Builds final track model with segments from centerline data.
"""

from dataclasses import dataclass, field
from typing import Optional, List
import math

from ..types.geometry import (
    TrackModel, TrackSegment, TrackPoint, CornerDirection, CornerApex
)
from ..types.confidence import Confidence


@dataclass
class GeometryBuilderConfig:
    """Configuration for geometry building."""
    
    # Segmentation
    min_segment_length_m: float = 20.0
    max_segment_length_m: float = 100.0
    
    # Corner detection
    corner_curvature_threshold: float = 0.005  # 1/200m radius
    straight_curvature_threshold: float = 0.001  # 1/1000m radius
    
    # Segment smoothing
    smoothing_window: int = 5
    
    # Apex detection
    apex_search_distance_m: float = 50.0


class TrackGeometryBuilder:
    """
    Builds track segments and identifies corners from centerline.
    
    Process:
    1. Smooth curvature data
    2. Segment track into straights and corners
    3. Identify apex points in corners
    4. Compute segment properties
    """
    
    def __init__(self, config: Optional[GeometryBuilderConfig] = None):
        self.config = config or GeometryBuilderConfig()
    
    def build_segments(self, track: TrackModel) -> TrackModel:
        """
        Build segments for a track model.
        
        Args:
            track: Track model with centerline
            
        Returns:
            Updated track model with segments
        """
        if not track.centerline:
            return track
        
        # Smooth curvature
        smoothed_points = self._smooth_curvature(track.centerline)
        
        # Detect segment boundaries
        boundaries = self._detect_segment_boundaries(smoothed_points)
        
        # Create segments
        segments = self._create_segments(smoothed_points, boundaries)
        
        # Identify corners
        segments = self._classify_segments(segments)
        
        # Name corners
        segments = self._name_corners(segments)
        
        # Update track model
        track.centerline = smoothed_points
        track.segments = segments
        
        return track
    
    def _smooth_curvature(
        self,
        points: List[TrackPoint]
    ) -> List[TrackPoint]:
        """Apply smoothing to curvature values."""
        
        if len(points) < self.config.smoothing_window:
            return points
        
        half_window = self.config.smoothing_window // 2
        smoothed = []
        
        for i in range(len(points)):
            # Get window bounds
            start = max(0, i - half_window)
            end = min(len(points), i + half_window + 1)
            
            # Average curvature in window
            window_curvatures = [points[j].curvature_1_per_m for j in range(start, end)]
            avg_curvature = sum(window_curvatures) / len(window_curvatures)
            
            smoothed.append(TrackPoint(
                latitude_deg=points[i].latitude_deg,
                longitude_deg=points[i].longitude_deg,
                altitude_m=points[i].altitude_m,
                distance_m=points[i].distance_m,
                curvature_1_per_m=avg_curvature,
                heading_deg=points[i].heading_deg,
                position_confidence=points[i].position_confidence,
                curvature_confidence=points[i].curvature_confidence
            ))
        
        return smoothed
    
    def _detect_segment_boundaries(
        self,
        points: List[TrackPoint]
    ) -> List[int]:
        """Detect indices where segment type changes."""
        
        if len(points) < 2:
            return [0, len(points) - 1]
        
        boundaries = [0]
        
        in_corner = abs(points[0].curvature_1_per_m) > self.config.corner_curvature_threshold
        segment_start = 0
        
        for i in range(1, len(points)):
            current_in_corner = abs(points[i].curvature_1_per_m) > self.config.corner_curvature_threshold
            
            # Check if segment type changed
            if current_in_corner != in_corner:
                # Check minimum segment length
                segment_length = points[i].distance_m - points[segment_start].distance_m
                
                if segment_length >= self.config.min_segment_length_m:
                    boundaries.append(i)
                    segment_start = i
                    in_corner = current_in_corner
            
            # Check maximum segment length
            segment_length = points[i].distance_m - points[segment_start].distance_m
            
            if segment_length >= self.config.max_segment_length_m:
                boundaries.append(i)
                segment_start = i
        
        # Ensure last point is a boundary
        if boundaries[-1] != len(points) - 1:
            boundaries.append(len(points) - 1)
        
        return boundaries
    
    def _create_segments(
        self,
        points: List[TrackPoint],
        boundaries: List[int]
    ) -> List[TrackSegment]:
        """Create segments from boundary indices."""
        
        segments = []
        
        for i in range(len(boundaries) - 1):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1]
            
            segment_points = points[start_idx:end_idx + 1]
            
            if not segment_points:
                continue
            
            # Compute segment properties
            avg_curvature = sum(p.curvature_1_per_m for p in segment_points) / len(segment_points)
            max_abs_curvature = max(abs(p.curvature_1_per_m) for p in segment_points)
            min_radius = 1.0 / max_abs_curvature if max_abs_curvature > 0 else float('inf')
            
            # Compute heading change
            heading_change = self._compute_heading_change(segment_points)
            
            # Compute average confidence
            avg_conf = sum(p.overall_confidence for p in segment_points) / len(segment_points)
            
            segment = TrackSegment(
                segment_id=i,
                start_distance_m=segment_points[0].distance_m,
                end_distance_m=segment_points[-1].distance_m,
                average_curvature_1_per_m=avg_curvature,
                minimum_radius_m=min_radius,
                average_heading_deg=segment_points[len(segment_points)//2].heading_deg,
                heading_change_deg=heading_change,
                points=segment_points,
                geometry_confidence=avg_conf
            )
            
            segments.append(segment)
        
        return segments
    
    def _classify_segments(
        self,
        segments: List[TrackSegment]
    ) -> List[TrackSegment]:
        """Classify segments as corners or straights."""
        
        classified = []
        
        for segment in segments:
            is_corner = abs(segment.average_curvature_1_per_m) > self.config.corner_curvature_threshold
            
            if is_corner:
                direction = (
                    CornerDirection.LEFT
                    if segment.average_curvature_1_per_m > 0
                    else CornerDirection.RIGHT
                )
            else:
                direction = CornerDirection.STRAIGHT
            
            classified_segment = TrackSegment(
                segment_id=segment.segment_id,
                start_distance_m=segment.start_distance_m,
                end_distance_m=segment.end_distance_m,
                is_corner=is_corner,
                direction=direction,
                average_curvature_1_per_m=segment.average_curvature_1_per_m,
                minimum_radius_m=segment.minimum_radius_m,
                average_heading_deg=segment.average_heading_deg,
                heading_change_deg=segment.heading_change_deg,
                points=segment.points,
                geometry_confidence=segment.geometry_confidence
            )
            
            classified.append(classified_segment)
        
        return classified
    
    def _name_corners(
        self,
        segments: List[TrackSegment]
    ) -> List[TrackSegment]:
        """Assign names to corner segments."""
        
        corner_number = 0
        named = []
        
        for segment in segments:
            if segment.is_corner:
                corner_number += 1
                
                # Determine corner type based on heading change
                abs_heading_change = abs(segment.heading_change_deg)
                
                if abs_heading_change > 150:
                    corner_type = "Hairpin"
                elif abs_heading_change > 90:
                    corner_type = f"Turn {corner_number}"
                elif abs_heading_change > 45:
                    corner_type = f"Turn {corner_number}"
                else:
                    corner_type = f"Kink {corner_number}"
                
                segment.corner_name = corner_type
            
            named.append(segment)
        
        return named
    
    def _compute_heading_change(
        self,
        points: List[TrackPoint]
    ) -> float:
        """Compute total heading change through a segment."""
        
        if len(points) < 2:
            return 0.0
        
        total_change = 0.0
        
        for i in range(1, len(points)):
            change = points[i].heading_deg - points[i-1].heading_deg
            
            # Normalize to -180 to 180
            while change > 180:
                change -= 360
            while change < -180:
                change += 360
            
            total_change += change
        
        return total_change
    
    def find_apex_points(self, track: TrackModel) -> List[CornerApex]:
        """
        Find apex points in corner segments.
        
        The apex is the point of maximum curvature in the corner.
        """
        apexes = []
        
        for segment in track.segments:
            if not segment.is_corner:
                continue
            
            # Find point of maximum curvature
            max_curvature = 0.0
            apex_point = None
            
            for point in segment.points:
                abs_curvature = abs(point.curvature_1_per_m)
                
                if abs_curvature > max_curvature:
                    max_curvature = abs_curvature
                    apex_point = point
            
            if apex_point:
                apex = CornerApex(
                    segment_id=segment.segment_id,
                    apex_distance_m=apex_point.distance_m,
                    apex_curvature_1_per_m=apex_point.curvature_1_per_m,
                    corner_direction=segment.direction,
                    minimum_radius_m=segment.minimum_radius_m,
                    entry_distance_m=segment.start_distance_m,
                    exit_distance_m=segment.end_distance_m,
                    confidence=apex_point.curvature_confidence
                )
                apexes.append(apex)
        
        return apexes
