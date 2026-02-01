"""
Segment Statistics
Safety-Critical Adaptive AI Race Coaching System

Stores per-segment statistics from clean laps for learning.

SAFETY INVARIANT S4: Physics models are hard ceilings.
Learning may only reduce conservatism, never exceed physics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime


@dataclass
class SegmentObservation:
    """Single observation of driver behavior in a segment."""
    
    segment_id: int
    timestamp: datetime
    
    # Observed values
    entry_speed_kmh: float
    apex_speed_kmh: float
    exit_speed_kmh: float
    
    min_speed_kmh: float
    max_lateral_g: float
    max_longitudinal_g: float
    
    # Braking
    brake_point_distance_m: float  # From segment start
    brake_intensity_peak: float    # 0-1
    
    # Steering
    max_steering_rate_deg_s: float
    
    # Quality indicators
    was_clean: bool = True  # No corrections, smooth inputs
    was_full_commitment: bool = False  # Driver was pushing
    confidence: float = 0.0  # Sensor confidence during segment


@dataclass
class SegmentStatistics:
    """
    Aggregated statistics for a track segment.
    
    These represent what the driver HAS done, not what they SHOULD do.
    They may only be used to REDUCE conservatism, never to exceed physics.
    """
    
    segment_id: int
    observation_count: int = 0
    
    # Speed statistics (from clean laps only)
    entry_speed_mean_kmh: float = 0.0
    entry_speed_std_kmh: float = 0.0
    entry_speed_max_kmh: float = 0.0
    
    apex_speed_mean_kmh: float = 0.0
    apex_speed_std_kmh: float = 0.0
    apex_speed_max_kmh: float = 0.0
    
    exit_speed_mean_kmh: float = 0.0
    exit_speed_std_kmh: float = 0.0
    exit_speed_max_kmh: float = 0.0
    
    # Braking statistics
    brake_point_mean_m: float = 0.0
    brake_point_std_m: float = 0.0
    brake_point_latest_m: float = 0.0  # Latest safe brake point observed
    
    # G-force statistics
    max_lateral_g_observed: float = 0.0
    max_longitudinal_g_observed: float = 0.0
    
    # Learning metadata
    first_observation: Optional[datetime] = None
    last_observation: Optional[datetime] = None
    confidence_weighted_count: float = 0.0
    
    # Decay factor (0-1, where 1 = full trust)
    decay_factor: float = 1.0
    
    @property
    def effective_observation_count(self) -> float:
        """Observation count adjusted for decay."""
        return self.confidence_weighted_count * self.decay_factor
    
    @property
    def has_sufficient_data(self) -> bool:
        """Check if enough observations for learning."""
        # Need at least 3 clean observations
        return self.effective_observation_count >= 3.0
    
    def get_learned_entry_speed(self, physics_ceiling_kmh: float) -> float:
        """
        Get learned entry speed, capped by physics ceiling.
        
        SAFETY: Never returns a value exceeding physics_ceiling_kmh.
        """
        if not self.has_sufficient_data:
            return physics_ceiling_kmh  # Use conservative physics limit
        
        # Use 95th percentile estimate (mean + 2*std), but cap at observed max
        learned = min(
            self.entry_speed_mean_kmh + 2 * self.entry_speed_std_kmh,
            self.entry_speed_max_kmh
        )
        
        # SAFETY: Never exceed physics ceiling
        return min(learned * self.decay_factor, physics_ceiling_kmh)
    
    def get_learned_brake_point(self, physics_minimum_m: float) -> float:
        """
        Get learned brake point, constrained by physics.
        
        SAFETY: Never returns a value later than physics_minimum_m.
        """
        if not self.has_sufficient_data:
            return physics_minimum_m  # Use conservative physics limit
        
        # Use earlier of: observed latest, or mean - 1 std
        conservative_learned = max(
            self.brake_point_latest_m,
            self.brake_point_mean_m - self.brake_point_std_m
        )
        
        # SAFETY: Never brake later than physics allows
        # Earlier is safer, so we take max (larger distance = earlier braking)
        return max(conservative_learned, physics_minimum_m)


class SegmentStatsStore:
    """
    Storage for segment statistics across all segments.
    
    Manages persistence and retrieval of learned behavior.
    """
    
    def __init__(self, max_observations_per_segment: int = 100):
        self._stats: Dict[int, SegmentStatistics] = {}
        self._observations: Dict[int, List[SegmentObservation]] = {}
        self._max_observations = max_observations_per_segment
    
    def add_observation(self, observation: SegmentObservation) -> None:
        """
        Add a new observation for a segment.
        
        Only clean laps with sufficient confidence are stored.
        """
        if not observation.was_clean:
            return  # Reject dirty observations
        
        if observation.confidence < 0.7:
            return  # Reject low-confidence observations
        
        segment_id = observation.segment_id
        
        # Initialize if needed
        if segment_id not in self._observations:
            self._observations[segment_id] = []
            self._stats[segment_id] = SegmentStatistics(segment_id=segment_id)
        
        # Add observation
        obs_list = self._observations[segment_id]
        obs_list.append(observation)
        
        # Trim old observations if needed
        if len(obs_list) > self._max_observations:
            obs_list.pop(0)
        
        # Update statistics
        self._update_statistics(segment_id)
    
    def _update_statistics(self, segment_id: int) -> None:
        """Recompute statistics from observations."""
        
        observations = self._observations.get(segment_id, [])
        if not observations:
            return
        
        stats = self._stats[segment_id]
        
        # Extract arrays
        entry_speeds = np.array([o.entry_speed_kmh for o in observations])
        apex_speeds = np.array([o.apex_speed_kmh for o in observations])
        exit_speeds = np.array([o.exit_speed_kmh for o in observations])
        brake_points = np.array([o.brake_point_distance_m for o in observations])
        lateral_gs = np.array([o.max_lateral_g for o in observations])
        long_gs = np.array([o.max_longitudinal_g for o in observations])
        confidences = np.array([o.confidence for o in observations])
        
        # Update counts
        stats.observation_count = len(observations)
        stats.confidence_weighted_count = np.sum(confidences)
        
        # Entry speed
        stats.entry_speed_mean_kmh = float(np.mean(entry_speeds))
        stats.entry_speed_std_kmh = float(np.std(entry_speeds))
        stats.entry_speed_max_kmh = float(np.max(entry_speeds))
        
        # Apex speed
        stats.apex_speed_mean_kmh = float(np.mean(apex_speeds))
        stats.apex_speed_std_kmh = float(np.std(apex_speeds))
        stats.apex_speed_max_kmh = float(np.max(apex_speeds))
        
        # Exit speed
        stats.exit_speed_mean_kmh = float(np.mean(exit_speeds))
        stats.exit_speed_std_kmh = float(np.std(exit_speeds))
        stats.exit_speed_max_kmh = float(np.max(exit_speeds))
        
        # Brake points
        stats.brake_point_mean_m = float(np.mean(brake_points))
        stats.brake_point_std_m = float(np.std(brake_points))
        stats.brake_point_latest_m = float(np.min(brake_points))  # Smallest distance = latest point
        
        # G-forces
        stats.max_lateral_g_observed = float(np.max(lateral_gs))
        stats.max_longitudinal_g_observed = float(np.max(long_gs))
        
        # Timestamps
        stats.first_observation = observations[0].timestamp
        stats.last_observation = observations[-1].timestamp
    
    def get_statistics(self, segment_id: int) -> Optional[SegmentStatistics]:
        """Get statistics for a segment."""
        return self._stats.get(segment_id)
    
    def apply_decay(self, segment_id: int, decay_factor: float) -> None:
        """Apply decay to segment statistics."""
        if segment_id in self._stats:
            self._stats[segment_id].decay_factor = decay_factor
    
    def apply_global_decay(self, decay_factor: float) -> None:
        """Apply decay to all segments."""
        for stats in self._stats.values():
            stats.decay_factor = decay_factor
    
    def get_all_segments(self) -> List[int]:
        """Get all segment IDs with statistics."""
        return list(self._stats.keys())
    
    def clear_segment(self, segment_id: int) -> None:
        """Clear all data for a segment."""
        self._observations.pop(segment_id, None)
        self._stats.pop(segment_id, None)
    
    def clear_all(self) -> None:
        """Clear all stored data."""
        self._observations.clear()
        self._stats.clear()
    
    def export(self) -> dict:
        """Export all statistics (for persistence)."""
        return {
            segment_id: {
                "observation_count": stats.observation_count,
                "entry_speed_mean_kmh": stats.entry_speed_mean_kmh,
                "entry_speed_std_kmh": stats.entry_speed_std_kmh,
                "entry_speed_max_kmh": stats.entry_speed_max_kmh,
                "apex_speed_mean_kmh": stats.apex_speed_mean_kmh,
                "brake_point_mean_m": stats.brake_point_mean_m,
                "brake_point_latest_m": stats.brake_point_latest_m,
                "max_lateral_g_observed": stats.max_lateral_g_observed,
                "decay_factor": stats.decay_factor,
            }
            for segment_id, stats in self._stats.items()
        }
