"""
Lap Validator
Safety-Critical Adaptive AI Race Coaching System

Validates laps before they can be used for learning.

SAFETY: Only clean, high-confidence laps may influence learned envelopes.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple

from ..types.telemetry import LapData, TelemetryFrame
from ..types.confidence import Confidence


class LapRejectionReason(Enum):
    """Reasons a lap may be rejected for learning."""
    
    NONE = auto()  # Lap accepted
    
    # Confidence issues
    LOW_OVERALL_CONFIDENCE = auto()
    CONFIDENCE_DROPOUT = auto()
    SENSOR_DISAGREEMENT = auto()
    
    # Lap quality issues
    INCOMPLETE_LAP = auto()
    OFF_TRACK_EXCURSION = auto()
    SPIN_DETECTED = auto()
    COLLISION_DETECTED = auto()
    
    # Driver behavior issues
    ABRUPT_CORRECTIONS = auto()
    INCONSISTENT_LINES = auto()
    UNDER_DRIVING = auto()  # Too conservative to learn from
    
    # Environmental issues
    CONDITION_CHANGE = auto()
    SESSION_BOUNDARY = auto()


@dataclass
class LapValidationResult:
    """Result of lap validation."""
    
    is_valid: bool
    rejection_reason: LapRejectionReason
    rejection_details: str = ""
    
    # Quality metrics
    overall_confidence: float = 0.0
    min_confidence: float = 0.0
    clean_segment_ratio: float = 0.0
    
    # Segment-level results
    valid_segments: List[int] = None
    invalid_segments: List[int] = None
    
    def __post_init__(self):
        if self.valid_segments is None:
            self.valid_segments = []
        if self.invalid_segments is None:
            self.invalid_segments = []


@dataclass
class ValidationConfig:
    """Configuration for lap validation."""
    
    # Confidence thresholds
    min_overall_confidence: float = 0.8
    min_segment_confidence: float = 0.7
    max_confidence_dropout_ratio: float = 0.1
    
    # Lap completeness
    min_track_coverage_ratio: float = 0.95
    
    # Driver behavior
    max_steering_correction_count: int = 5
    max_yaw_rate_spike_count: int = 3
    max_lateral_g_spike_count: int = 3
    
    # Thresholds for spike detection
    steering_correction_threshold_deg_s: float = 100.0
    yaw_rate_spike_threshold_deg_s: float = 50.0
    lateral_g_spike_threshold: float = 0.5  # G change in <100ms


class LapValidator:
    """
    Validates laps before they can be used for learning.
    
    Only clean, high-confidence laps are eligible for Adaptive
    Envelope Refinement. This validator enforces strict quality
    criteria to prevent learning from bad data.
    
    SAFETY PRINCIPLE:
    - Bad data is worse than no data
    - Reject if in doubt
    - Conservative thresholds by default
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
    
    def validate_lap(self, lap_data: LapData) -> LapValidationResult:
        """
        Validate a complete lap for learning eligibility.
        
        Args:
            lap_data: Complete lap telemetry
            
        Returns:
            Validation result with acceptance/rejection details
        """
        # Check 1: Lap completeness
        result = self._check_completeness(lap_data)
        if not result.is_valid:
            return result
        
        # Check 2: Overall confidence
        result = self._check_confidence(lap_data)
        if not result.is_valid:
            return result
        
        # Check 3: Sensor consistency
        result = self._check_sensor_consistency(lap_data)
        if not result.is_valid:
            return result
        
        # Check 4: Driver behavior
        result = self._check_driver_behavior(lap_data)
        if not result.is_valid:
            return result
        
        # Check 5: Off-track / incidents
        result = self._check_for_incidents(lap_data)
        if not result.is_valid:
            return result
        
        # All checks passed
        valid_segments, invalid_segments = self._identify_valid_segments(lap_data)
        
        return LapValidationResult(
            is_valid=True,
            rejection_reason=LapRejectionReason.NONE,
            overall_confidence=self._compute_overall_confidence(lap_data),
            min_confidence=self._compute_min_confidence(lap_data),
            clean_segment_ratio=len(valid_segments) / max(len(valid_segments) + len(invalid_segments), 1),
            valid_segments=valid_segments,
            invalid_segments=invalid_segments
        )
    
    def _check_completeness(self, lap_data: LapData) -> LapValidationResult:
        """Check if lap is complete."""
        
        # Check frame count (minimum viable lap)
        if len(lap_data.frames) < 100:
            return LapValidationResult(
                is_valid=False,
                rejection_reason=LapRejectionReason.INCOMPLETE_LAP,
                rejection_details=f"Too few frames: {len(lap_data.frames)}"
            )
        
        # Check track coverage
        if hasattr(lap_data, 'track_coverage_ratio'):
            if lap_data.track_coverage_ratio < self.config.min_track_coverage_ratio:
                return LapValidationResult(
                    is_valid=False,
                    rejection_reason=LapRejectionReason.INCOMPLETE_LAP,
                    rejection_details=f"Coverage: {lap_data.track_coverage_ratio:.1%}"
                )
        
        return LapValidationResult(is_valid=True, rejection_reason=LapRejectionReason.NONE)
    
    def _check_confidence(self, lap_data: LapData) -> LapValidationResult:
        """Check overall confidence levels."""
        
        confidences = [f.confidence for f in lap_data.frames if f.confidence is not None]
        
        if not confidences:
            return LapValidationResult(
                is_valid=False,
                rejection_reason=LapRejectionReason.LOW_OVERALL_CONFIDENCE,
                rejection_details="No confidence data"
            )
        
        overall_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        
        if overall_confidence < self.config.min_overall_confidence:
            return LapValidationResult(
                is_valid=False,
                rejection_reason=LapRejectionReason.LOW_OVERALL_CONFIDENCE,
                rejection_details=f"Overall: {overall_confidence:.2f}",
                overall_confidence=overall_confidence,
                min_confidence=min_confidence
            )
        
        # Check for dropouts
        dropout_count = sum(1 for c in confidences if c < self.config.min_segment_confidence)
        dropout_ratio = dropout_count / len(confidences)
        
        if dropout_ratio > self.config.max_confidence_dropout_ratio:
            return LapValidationResult(
                is_valid=False,
                rejection_reason=LapRejectionReason.CONFIDENCE_DROPOUT,
                rejection_details=f"Dropout ratio: {dropout_ratio:.1%}",
                overall_confidence=overall_confidence,
                min_confidence=min_confidence
            )
        
        return LapValidationResult(
            is_valid=True,
            rejection_reason=LapRejectionReason.NONE,
            overall_confidence=overall_confidence,
            min_confidence=min_confidence
        )
    
    def _check_sensor_consistency(self, lap_data: LapData) -> LapValidationResult:
        """Check for sensor disagreement."""
        
        # Look for frames with sensor disagreement flag
        disagreement_count = sum(
            1 for f in lap_data.frames
            if hasattr(f, 'sensor_disagreement') and f.sensor_disagreement
        )
        
        disagreement_ratio = disagreement_count / len(lap_data.frames)
        
        if disagreement_ratio > 0.05:  # More than 5% disagreement
            return LapValidationResult(
                is_valid=False,
                rejection_reason=LapRejectionReason.SENSOR_DISAGREEMENT,
                rejection_details=f"Disagreement ratio: {disagreement_ratio:.1%}"
            )
        
        return LapValidationResult(is_valid=True, rejection_reason=LapRejectionReason.NONE)
    
    def _check_driver_behavior(self, lap_data: LapData) -> LapValidationResult:
        """Check for abrupt corrections indicating driver mistakes."""
        
        correction_count = 0
        yaw_spike_count = 0
        g_spike_count = 0
        
        prev_frame = None
        for frame in lap_data.frames:
            if prev_frame is None:
                prev_frame = frame
                continue
            
            # Time delta
            dt_s = (frame.timestamp_ms - prev_frame.timestamp_ms) / 1000.0
            if dt_s <= 0:
                continue
            
            # Check steering rate
            if hasattr(frame, 'steering_angle_deg') and hasattr(prev_frame, 'steering_angle_deg'):
                steering_rate = abs(frame.steering_angle_deg - prev_frame.steering_angle_deg) / dt_s
                if steering_rate > self.config.steering_correction_threshold_deg_s:
                    correction_count += 1
            
            # Check yaw rate spikes
            if hasattr(frame, 'yaw_rate_deg_s') and hasattr(prev_frame, 'yaw_rate_deg_s'):
                yaw_change = abs(frame.yaw_rate_deg_s - prev_frame.yaw_rate_deg_s) / dt_s
                if yaw_change > self.config.yaw_rate_spike_threshold_deg_s:
                    yaw_spike_count += 1
            
            # Check lateral G spikes
            if hasattr(frame, 'lateral_g') and hasattr(prev_frame, 'lateral_g'):
                if dt_s < 0.15:  # Only short intervals
                    g_change = abs(frame.lateral_g - prev_frame.lateral_g)
                    if g_change > self.config.lateral_g_spike_threshold:
                        g_spike_count += 1
            
            prev_frame = frame
        
        # Evaluate counts
        if correction_count > self.config.max_steering_correction_count:
            return LapValidationResult(
                is_valid=False,
                rejection_reason=LapRejectionReason.ABRUPT_CORRECTIONS,
                rejection_details=f"Steering corrections: {correction_count}"
            )
        
        if yaw_spike_count > self.config.max_yaw_rate_spike_count:
            return LapValidationResult(
                is_valid=False,
                rejection_reason=LapRejectionReason.SPIN_DETECTED,
                rejection_details=f"Yaw spikes: {yaw_spike_count}"
            )
        
        if g_spike_count > self.config.max_lateral_g_spike_count:
            return LapValidationResult(
                is_valid=False,
                rejection_reason=LapRejectionReason.ABRUPT_CORRECTIONS,
                rejection_details=f"G-force spikes: {g_spike_count}"
            )
        
        return LapValidationResult(is_valid=True, rejection_reason=LapRejectionReason.NONE)
    
    def _check_for_incidents(self, lap_data: LapData) -> LapValidationResult:
        """Check for off-track excursions or incidents."""
        
        for frame in lap_data.frames:
            # Check off-track flag
            if hasattr(frame, 'off_track') and frame.off_track:
                return LapValidationResult(
                    is_valid=False,
                    rejection_reason=LapRejectionReason.OFF_TRACK_EXCURSION,
                    rejection_details="Off-track detected"
                )
            
            # Check for impact signature (sudden deceleration)
            if hasattr(frame, 'longitudinal_g'):
                if frame.longitudinal_g < -2.5:  # Very hard braking or impact
                    return LapValidationResult(
                        is_valid=False,
                        rejection_reason=LapRejectionReason.COLLISION_DETECTED,
                        rejection_details=f"Decel: {frame.longitudinal_g:.1f}g"
                    )
        
        return LapValidationResult(is_valid=True, rejection_reason=LapRejectionReason.NONE)
    
    def _identify_valid_segments(self, lap_data: LapData) -> Tuple[List[int], List[int]]:
        """Identify which segments are valid for learning."""
        
        valid_segments = []
        invalid_segments = []
        
        # Group frames by segment
        segment_frames = {}
        for frame in lap_data.frames:
            if hasattr(frame, 'segment_id'):
                seg_id = frame.segment_id
                if seg_id not in segment_frames:
                    segment_frames[seg_id] = []
                segment_frames[seg_id].append(frame)
        
        # Validate each segment
        for seg_id, frames in segment_frames.items():
            # Check segment confidence
            confidences = [f.confidence for f in frames if f.confidence is not None]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
                if avg_confidence >= self.config.min_segment_confidence:
                    valid_segments.append(seg_id)
                else:
                    invalid_segments.append(seg_id)
            else:
                invalid_segments.append(seg_id)
        
        return valid_segments, invalid_segments
    
    def _compute_overall_confidence(self, lap_data: LapData) -> float:
        """Compute overall lap confidence."""
        confidences = [f.confidence for f in lap_data.frames if f.confidence is not None]
        if not confidences:
            return 0.0
        return sum(confidences) / len(confidences)
    
    def _compute_min_confidence(self, lap_data: LapData) -> float:
        """Compute minimum confidence across lap."""
        confidences = [f.confidence for f in lap_data.frames if f.confidence is not None]
        if not confidences:
            return 0.0
        return min(confidences)
