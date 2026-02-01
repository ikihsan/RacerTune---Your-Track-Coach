"""
Driven Laps Track Creation
Safety-Critical Adaptive AI Race Coaching System

Creates track geometry from driven GPS laps with averaging and outlier rejection.

METHOD 1: Multiple driven laps with distance-based alignment.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import math

from ..types.geometry import TrackPoint, TrackModel
from ..types.telemetry import LapData, TelemetryFrame
from ..types.confidence import Confidence


@dataclass
class DrivenLapConfig:
    """Configuration for driven lap processing."""
    
    # Minimum laps for track creation
    min_laps_for_creation: int = 3
    
    # Point spacing
    target_point_spacing_m: float = 5.0
    
    # Outlier rejection
    outlier_std_multiplier: float = 2.0
    
    # Alignment
    alignment_distance_tolerance_m: float = 10.0
    
    # Start/finish detection
    start_finish_proximity_m: float = 20.0
    min_lap_length_m: float = 500.0
    
    # Quality requirements
    min_average_confidence: float = 0.6
    min_point_confidence: float = 0.4


class DrivenLapProcessor:
    """
    Processes multiple driven laps to create track geometry.
    
    Algorithm:
    1. Detect start/finish line crossing
    2. Align laps by distance from start
    3. Average positions at each distance point
    4. Reject outlier points
    5. Compute curvature from averaged centerline
    
    SAFETY:
    - Requires multiple laps for confidence
    - Outliers are rejected, not averaged
    - Confidence reflects data quality
    """
    
    def __init__(self, config: Optional[DrivenLapConfig] = None):
        self.config = config or DrivenLapConfig()
        
        # Storage
        self._laps: List[List[TrackPoint]] = []
        self._start_finish_position: Optional[Tuple[float, float]] = None
        
    def add_lap(self, lap: LapData) -> bool:
        """
        Add a lap to the track creation dataset.
        
        Args:
            lap: Completed lap data
            
        Returns:
            True if lap was accepted
        """
        # Validate lap
        if not self._validate_lap(lap):
            return False
        
        # Convert to track points
        points = self._convert_lap_to_points(lap)
        
        if not points:
            return False
        
        # Detect start/finish if not set
        if self._start_finish_position is None:
            self._start_finish_position = (
                points[0].latitude_deg,
                points[0].longitude_deg
            )
        
        # Align to start/finish
        aligned_points = self._align_to_start_finish(points)
        
        if aligned_points:
            self._laps.append(aligned_points)
            return True
        
        return False
    
    def can_create_track(self) -> bool:
        """Check if enough data exists to create track."""
        return len(self._laps) >= self.config.min_laps_for_creation
    
    def create_track(self, track_id: str, track_name: str) -> Optional[TrackModel]:
        """
        Create track model from collected laps.
        
        Returns:
            TrackModel if successful, None otherwise
        """
        if not self.can_create_track():
            return None
        
        # Compute total distance from first lap
        total_distance = self._compute_total_distance(self._laps[0])
        
        if total_distance < self.config.min_lap_length_m:
            return None
        
        # Create distance-indexed points
        distance_points = self._create_distance_indexed_points(total_distance)
        
        # Average across laps
        averaged_points = self._average_points_across_laps(distance_points)
        
        # Compute curvature
        points_with_curvature = self._compute_curvature(averaged_points)
        
        # Compute confidence
        track_confidence = self._compute_track_confidence(points_with_curvature)
        
        # Build track model
        track = TrackModel(
            track_id=track_id,
            track_name=track_name,
            total_length_m=total_distance,
            creation_timestamp_ms=0,  # Set by caller
            gps_laps_used=len(self._laps),
            centerline=points_with_curvature,
            geometry_confidence=track_confidence
        )
        
        # Set start/finish
        if self._start_finish_position:
            track.start_finish_latitude_deg = self._start_finish_position[0]
            track.start_finish_longitude_deg = self._start_finish_position[1]
        
        return track
    
    def _validate_lap(self, lap: LapData) -> bool:
        """Validate that lap is suitable for track creation."""
        
        if not lap.is_complete:
            return False
        
        if lap.average_confidence < self.config.min_average_confidence:
            return False
        
        if lap.frame_count < 10:
            return False
        
        return True
    
    def _convert_lap_to_points(self, lap: LapData) -> List[TrackPoint]:
        """Convert lap frames to track points."""
        
        points = []
        cumulative_distance = 0.0
        last_lat = None
        last_lon = None
        
        for frame in lap.frames:
            if not frame.has_fused:
                continue
            
            fused = frame.fused
            
            if fused.position_confidence.value < self.config.min_point_confidence:
                continue
            
            lat = fused.latitude_deg
            lon = fused.longitude_deg
            
            # Compute distance from last point
            if last_lat is not None:
                distance = self._haversine_distance(last_lat, last_lon, lat, lon)
                cumulative_distance += distance
            
            points.append(TrackPoint(
                latitude_deg=lat,
                longitude_deg=lon,
                altitude_m=fused.altitude_m,
                distance_m=cumulative_distance,
                heading_deg=fused.heading_deg,
                position_confidence=fused.position_confidence.value
            ))
            
            last_lat = lat
            last_lon = lon
        
        return points
    
    def _align_to_start_finish(
        self,
        points: List[TrackPoint]
    ) -> List[TrackPoint]:
        """Align lap to start/finish position."""
        
        if not self._start_finish_position:
            return points
        
        sf_lat, sf_lon = self._start_finish_position
        
        # Find closest point to start/finish
        min_distance = float('inf')
        start_index = 0
        
        for i, point in enumerate(points):
            distance = self._haversine_distance(
                sf_lat, sf_lon,
                point.latitude_deg, point.longitude_deg
            )
            if distance < min_distance:
                min_distance = distance
                start_index = i
        
        # Check if close enough
        if min_distance > self.config.start_finish_proximity_m:
            return []  # Lap doesn't pass through start/finish
        
        # Rotate points to start at start/finish
        rotated = points[start_index:] + points[:start_index]
        
        # Recompute distances from new start
        cumulative_distance = 0.0
        aligned = []
        
        for i, point in enumerate(rotated):
            if i > 0:
                cumulative_distance += self._haversine_distance(
                    rotated[i-1].latitude_deg, rotated[i-1].longitude_deg,
                    point.latitude_deg, point.longitude_deg
                )
            
            aligned.append(TrackPoint(
                latitude_deg=point.latitude_deg,
                longitude_deg=point.longitude_deg,
                altitude_m=point.altitude_m,
                distance_m=cumulative_distance,
                heading_deg=point.heading_deg,
                position_confidence=point.position_confidence
            ))
        
        return aligned
    
    def _compute_total_distance(self, points: List[TrackPoint]) -> float:
        """Compute total track distance."""
        if not points:
            return 0.0
        return points[-1].distance_m
    
    def _create_distance_indexed_points(
        self,
        total_distance: float
    ) -> List[float]:
        """Create list of distance values for interpolation."""
        
        distances = []
        current = 0.0
        
        while current < total_distance:
            distances.append(current)
            current += self.config.target_point_spacing_m
        
        return distances
    
    def _average_points_across_laps(
        self,
        target_distances: List[float]
    ) -> List[TrackPoint]:
        """Average point positions across all laps at each distance."""
        
        averaged_points = []
        
        for target_distance in target_distances:
            # Collect points from each lap at this distance
            lat_values = []
            lon_values = []
            alt_values = []
            heading_values = []
            confidence_values = []
            
            for lap_points in self._laps:
                # Interpolate point at this distance
                interpolated = self._interpolate_at_distance(lap_points, target_distance)
                
                if interpolated:
                    lat_values.append(interpolated.latitude_deg)
                    lon_values.append(interpolated.longitude_deg)
                    if interpolated.altitude_m is not None:
                        alt_values.append(interpolated.altitude_m)
                    heading_values.append(interpolated.heading_deg)
                    confidence_values.append(interpolated.position_confidence)
            
            if len(lat_values) < 2:
                continue
            
            # Reject outliers using IQR method
            lat_clean = self._reject_outliers(lat_values)
            lon_clean = self._reject_outliers(lon_values)
            
            if not lat_clean or not lon_clean:
                continue
            
            # Average remaining values
            avg_lat = sum(lat_clean) / len(lat_clean)
            avg_lon = sum(lon_clean) / len(lon_clean)
            avg_alt = sum(alt_values) / len(alt_values) if alt_values else None
            
            # Average heading (circular mean)
            avg_heading = self._circular_mean(heading_values)
            
            # Confidence based on spread and sample count
            avg_confidence = sum(confidence_values) / len(confidence_values)
            spread_penalty = min(1.0, len(lat_clean) / len(lat_values))
            final_confidence = avg_confidence * spread_penalty
            
            averaged_points.append(TrackPoint(
                latitude_deg=avg_lat,
                longitude_deg=avg_lon,
                altitude_m=avg_alt,
                distance_m=target_distance,
                heading_deg=avg_heading,
                position_confidence=final_confidence
            ))
        
        return averaged_points
    
    def _interpolate_at_distance(
        self,
        points: List[TrackPoint],
        target_distance: float
    ) -> Optional[TrackPoint]:
        """Interpolate a point at the given distance."""
        
        if not points:
            return None
        
        # Find surrounding points
        for i in range(len(points) - 1):
            if points[i].distance_m <= target_distance < points[i+1].distance_m:
                # Linear interpolation
                p1 = points[i]
                p2 = points[i+1]
                
                if p2.distance_m == p1.distance_m:
                    t = 0.5
                else:
                    t = (target_distance - p1.distance_m) / (p2.distance_m - p1.distance_m)
                
                return TrackPoint(
                    latitude_deg=p1.latitude_deg + t * (p2.latitude_deg - p1.latitude_deg),
                    longitude_deg=p1.longitude_deg + t * (p2.longitude_deg - p1.longitude_deg),
                    altitude_m=(
                        p1.altitude_m + t * (p2.altitude_m - p1.altitude_m)
                        if p1.altitude_m and p2.altitude_m else None
                    ),
                    distance_m=target_distance,
                    heading_deg=p1.heading_deg + t * (p2.heading_deg - p1.heading_deg),
                    position_confidence=min(p1.position_confidence, p2.position_confidence)
                )
        
        return None
    
    def _reject_outliers(self, values: List[float]) -> List[float]:
        """Reject outliers using standard deviation method."""
        
        if len(values) < 3:
            return values
        
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)
        
        if std < 1e-9:
            return values
        
        threshold = self.config.outlier_std_multiplier * std
        
        return [v for v in values if abs(v - mean) <= threshold]
    
    def _circular_mean(self, angles: List[float]) -> float:
        """Compute circular mean of angles in degrees."""
        
        if not angles:
            return 0.0
        
        sin_sum = sum(math.sin(math.radians(a)) for a in angles)
        cos_sum = sum(math.cos(math.radians(a)) for a in angles)
        
        mean_rad = math.atan2(sin_sum, cos_sum)
        mean_deg = math.degrees(mean_rad)
        
        return (mean_deg + 360) % 360
    
    def _compute_curvature(
        self,
        points: List[TrackPoint]
    ) -> List[TrackPoint]:
        """Compute curvature at each point."""
        
        if len(points) < 3:
            return points
        
        result = []
        
        for i in range(len(points)):
            if i == 0:
                # First point - use forward difference
                curvature = self._compute_curvature_at_point(
                    points[0], points[1], points[2] if len(points) > 2 else points[1]
                )
            elif i == len(points) - 1:
                # Last point - use backward difference
                curvature = self._compute_curvature_at_point(
                    points[-3] if len(points) > 2 else points[-2],
                    points[-2], points[-1]
                )
            else:
                # Interior point - use three-point formula
                curvature = self._compute_curvature_at_point(
                    points[i-1], points[i], points[i+1]
                )
            
            result.append(TrackPoint(
                latitude_deg=points[i].latitude_deg,
                longitude_deg=points[i].longitude_deg,
                altitude_m=points[i].altitude_m,
                distance_m=points[i].distance_m,
                curvature_1_per_m=curvature,
                heading_deg=points[i].heading_deg,
                position_confidence=points[i].position_confidence,
                curvature_confidence=points[i].position_confidence * 0.8  # Lower confidence for derived value
            ))
        
        return result
    
    def _compute_curvature_at_point(
        self,
        p1: TrackPoint,
        p2: TrackPoint,
        p3: TrackPoint
    ) -> float:
        """
        Compute curvature at p2 using three points.
        
        Uses the Menger curvature formula:
        k = 4 * A / (a * b * c)
        where A is the area of the triangle and a, b, c are side lengths
        """
        # Convert to local Cartesian coordinates (approximate for small areas)
        lat_ref = p2.latitude_deg
        
        x1, y1 = self._to_local_coords(p1.latitude_deg, p1.longitude_deg, lat_ref)
        x2, y2 = self._to_local_coords(p2.latitude_deg, p2.longitude_deg, lat_ref)
        x3, y3 = self._to_local_coords(p3.latitude_deg, p3.longitude_deg, lat_ref)
        
        # Compute side lengths
        a = math.sqrt((x2 - x3)**2 + (y2 - y3)**2)
        b = math.sqrt((x1 - x3)**2 + (y1 - y3)**2)
        c = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        
        # Compute area using cross product
        area = abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)) / 2
        
        # Compute curvature
        denominator = a * b * c
        
        if denominator < 1e-9:
            return 0.0
        
        curvature = 4 * area / denominator
        
        # Determine sign (positive = left turn)
        cross = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
        if cross < 0:
            curvature = -curvature
        
        return curvature
    
    def _to_local_coords(
        self,
        lat: float,
        lon: float,
        lat_ref: float
    ) -> Tuple[float, float]:
        """Convert GPS to local Cartesian coordinates (meters)."""
        
        # Approximate conversion
        x = (lon - 0) * 111320 * math.cos(math.radians(lat_ref))
        y = lat * 110540
        
        return x, y
    
    def _compute_track_confidence(
        self,
        points: List[TrackPoint]
    ) -> Confidence:
        """Compute overall track confidence."""
        
        if not points:
            return Confidence(0.0, "track", 0, "no_points")
        
        # Average point confidence
        avg_conf = sum(p.position_confidence for p in points) / len(points)
        
        # Lap count factor
        lap_factor = min(1.0, len(self._laps) / 5)  # Full confidence at 5 laps
        
        # Final confidence
        final = avg_conf * lap_factor
        
        return Confidence(
            value=final,
            source="driven_laps",
            timestamp_ms=0,
            degradation_reason=None if final > 0.7 else f"laps:{len(self._laps)}"
        )
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Compute distance between two GPS coordinates in meters."""
        
        R = 6371000
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def reset(self) -> None:
        """Reset processor state."""
        self._laps.clear()
        self._start_finish_position = None
