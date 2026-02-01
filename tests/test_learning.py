"""
Test Learning System
Safety-Critical Adaptive AI Race Coaching System

Tests for the adaptive learning system.
"""

import pytest
from datetime import datetime

from src.learning.segment_stats import SegmentStatistics, SegmentStatsStore, SegmentObservation
from src.learning.lap_validator import LapValidator, LapRejectionReason
from src.learning.blend_engine import BlendEngine, BlendConfig
from src.learning.decay_manager import DecayManager, DecayTrigger, ConditionState
from src.types.envelopes import CornerSpeedEnvelope, BrakingEnvelope
from src.types.telemetry import LapData, TelemetryFrame


class TestSegmentStatistics:
    """Tests for segment statistics."""
    
    def test_insufficient_data_returns_physics(self):
        """With insufficient data, physics ceiling is used."""
        stats = SegmentStatistics(
            segment_id=1,
            observation_count=1,  # Not enough
            entry_speed_mean_kmh=120.0,
            confidence_weighted_count=1.0
        )
        
        physics_ceiling = 100.0
        learned = stats.get_learned_entry_speed(physics_ceiling)
        
        # Should return physics ceiling when insufficient data
        assert learned == physics_ceiling
    
    def test_sufficient_data_can_influence(self):
        """With sufficient data, learned values can influence."""
        stats = SegmentStatistics(
            segment_id=1,
            observation_count=10,
            entry_speed_mean_kmh=90.0,  # Below physics
            entry_speed_std_kmh=3.0,
            entry_speed_max_kmh=95.0,
            confidence_weighted_count=9.0,
            decay_factor=1.0
        )
        
        physics_ceiling = 100.0
        learned = stats.get_learned_entry_speed(physics_ceiling)
        
        # Should return something <= physics ceiling
        assert learned <= physics_ceiling
    
    def test_learned_never_exceeds_physics(self):
        """Learned speed never exceeds physics ceiling."""
        stats = SegmentStatistics(
            segment_id=1,
            observation_count=50,
            entry_speed_mean_kmh=150.0,  # Way above physics
            entry_speed_std_kmh=5.0,
            entry_speed_max_kmh=160.0,
            confidence_weighted_count=45.0
        )
        
        physics_ceiling = 100.0
        learned = stats.get_learned_entry_speed(physics_ceiling)
        
        # Must never exceed physics ceiling
        assert learned <= physics_ceiling


class TestSegmentStatsStore:
    """Tests for segment stats storage."""
    
    def test_dirty_observations_rejected(self):
        """Dirty observations are not stored."""
        store = SegmentStatsStore()
        
        observation = SegmentObservation(
            segment_id=1,
            timestamp=datetime.now(),
            entry_speed_kmh=100.0,
            apex_speed_kmh=80.0,
            exit_speed_kmh=90.0,
            min_speed_kmh=75.0,
            max_lateral_g=0.8,
            max_longitudinal_g=0.5,
            brake_point_distance_m=50.0,
            brake_intensity_peak=0.7,
            max_steering_rate_deg_s=50.0,
            was_clean=False,  # Dirty!
            confidence=0.9
        )
        
        store.add_observation(observation)
        
        # Should not have been stored
        stats = store.get_statistics(1)
        assert stats is None or stats.observation_count == 0
    
    def test_low_confidence_rejected(self):
        """Low confidence observations are not stored."""
        store = SegmentStatsStore()
        
        observation = SegmentObservation(
            segment_id=1,
            timestamp=datetime.now(),
            entry_speed_kmh=100.0,
            apex_speed_kmh=80.0,
            exit_speed_kmh=90.0,
            min_speed_kmh=75.0,
            max_lateral_g=0.8,
            max_longitudinal_g=0.5,
            brake_point_distance_m=50.0,
            brake_intensity_peak=0.7,
            max_steering_rate_deg_s=50.0,
            was_clean=True,
            confidence=0.5  # Too low
        )
        
        store.add_observation(observation)
        
        # Should not have been stored
        stats = store.get_statistics(1)
        assert stats is None or stats.observation_count == 0
    
    def test_clean_high_confidence_stored(self):
        """Clean, high-confidence observations are stored."""
        store = SegmentStatsStore()
        
        observation = SegmentObservation(
            segment_id=1,
            timestamp=datetime.now(),
            entry_speed_kmh=100.0,
            apex_speed_kmh=80.0,
            exit_speed_kmh=90.0,
            min_speed_kmh=75.0,
            max_lateral_g=0.8,
            max_longitudinal_g=0.5,
            brake_point_distance_m=50.0,
            brake_intensity_peak=0.7,
            max_steering_rate_deg_s=50.0,
            was_clean=True,
            confidence=0.9
        )
        
        store.add_observation(observation)
        
        stats = store.get_statistics(1)
        assert stats is not None
        assert stats.observation_count == 1


class TestBlendEngine:
    """Tests for envelope blending."""
    
    def test_no_learning_returns_physics(self):
        """Without learning data, physics is returned."""
        blend = BlendEngine()
        
        physics = CornerSpeedEnvelope(
            segment_id=1,
            max_speed_kmh=100.0,
            min_speed_kmh=50.0,
            confidence=0.95
        )
        
        result = blend.blend_corner_speed(physics, None)
        
        assert result.blended_value == physics.max_speed_kmh
        assert result.learned_weight == 0.0
    
    def test_learning_influence_is_bounded(self):
        """Learning influence is bounded by max setting."""
        config = BlendConfig(max_learned_influence=0.2)
        blend = BlendEngine(config)
        
        physics = CornerSpeedEnvelope(
            segment_id=1,
            max_speed_kmh=100.0,
            min_speed_kmh=50.0,
            confidence=0.95
        )
        
        stats = SegmentStatistics(
            segment_id=1,
            observation_count=100,
            entry_speed_mean_kmh=85.0,
            entry_speed_std_kmh=2.0,
            entry_speed_max_kmh=90.0,
            confidence_weighted_count=95.0
        )
        
        result = blend.blend_corner_speed(physics, stats)
        
        # Weight should not exceed 0.2
        assert result.learned_weight <= 0.2


class TestDecayManager:
    """Tests for learning decay."""
    
    def test_weather_change_triggers_decay(self):
        """Weather change triggers learning decay."""
        store = SegmentStatsStore()
        manager = DecayManager(stats_store=store)
        
        # Initial dry conditions
        dry_conditions = ConditionState(
            is_dry=True,
            last_activity=datetime.now()
        )
        manager.update_conditions(dry_conditions)
        
        # Change to wet
        wet_conditions = ConditionState(
            is_dry=False,
            last_activity=datetime.now()
        )
        
        decays = manager.update_conditions(wet_conditions)
        
        # Should trigger weather decay
        assert DecayTrigger.WEATHER_CHANGE in decays
        assert decays[DecayTrigger.WEATHER_CHANGE] == 0.0  # Complete reset
    
    def test_temperature_change_triggers_partial_decay(self):
        """Large temperature change triggers partial decay."""
        manager = DecayManager()
        
        # Initial conditions
        initial = ConditionState(
            track_temp_c=30.0,
            last_activity=datetime.now()
        )
        manager.update_conditions(initial)
        
        # Temperature change
        changed = ConditionState(
            track_temp_c=50.0,  # 20 degree change
            last_activity=datetime.now()
        )
        
        decays = manager.update_conditions(changed)
        
        # Should trigger temperature decay
        assert DecayTrigger.TEMPERATURE_CHANGE in decays
        # Partial decay (not complete reset)
        assert 0 < decays[DecayTrigger.TEMPERATURE_CHANGE] < 1.0


class TestLapValidator:
    """Tests for lap validation."""
    
    def test_incomplete_lap_rejected(self):
        """Incomplete laps are rejected."""
        validator = LapValidator()
        
        # Very short lap
        lap = LapData(
            lap_number=1,
            frames=[TelemetryFrame(timestamp_ms=i*100, confidence=0.9) for i in range(10)]
        )
        
        result = validator.validate_lap(lap)
        
        assert not result.is_valid
        assert result.rejection_reason == LapRejectionReason.INCOMPLETE_LAP
    
    def test_low_confidence_lap_rejected(self):
        """Low confidence laps are rejected."""
        validator = LapValidator()
        
        # Lap with low confidence
        lap = LapData(
            lap_number=1,
            frames=[TelemetryFrame(timestamp_ms=i*100, confidence=0.5) for i in range(200)]
        )
        
        result = validator.validate_lap(lap)
        
        assert not result.is_valid
        assert result.rejection_reason == LapRejectionReason.LOW_OVERALL_CONFIDENCE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
