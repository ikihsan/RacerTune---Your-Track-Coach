"""
Test Physics Calculations
Safety-Critical Adaptive AI Race Coaching System

Tests for physics-based calculations.
"""

import pytest
import math
from src.physics.corner_speed import CornerSpeedCalculator, CornerSpeedConfig
from src.physics.braking_envelope import BrakingCalculator, BrakingConfig
from src.types.geometry import TrackSegment


class TestCornerSpeedCalculator:
    """Tests for corner speed calculations."""
    
    def test_straight_line_speed_is_high(self):
        """Straight sections allow high speed."""
        calc = CornerSpeedCalculator()
        
        # Very large radius (straight)
        result = calc.compute_max_speed(
            radius_m=10000.0,
            friction_coefficient=1.0,
            banking_deg=0.0,
            segment_id=1
        )
        
        # Should be capped at some reasonable max
        assert result.max_speed_kmh > 200.0
    
    def test_tight_corner_limits_speed(self):
        """Tight corners limit speed."""
        calc = CornerSpeedCalculator()
        
        # Tight hairpin
        result = calc.compute_max_speed(
            radius_m=15.0,
            friction_coefficient=1.0,
            banking_deg=0.0,
            segment_id=1
        )
        
        # Should be relatively slow
        assert result.max_speed_kmh < 100.0
    
    def test_banking_increases_speed(self):
        """Positive banking increases cornering speed."""
        calc = CornerSpeedCalculator()
        
        # Without banking
        flat_result = calc.compute_max_speed(
            radius_m=50.0,
            friction_coefficient=1.0,
            banking_deg=0.0,
            segment_id=1
        )
        
        # With banking
        banked_result = calc.compute_max_speed(
            radius_m=50.0,
            friction_coefficient=1.0,
            banking_deg=15.0,
            segment_id=1
        )
        
        assert banked_result.max_speed_kmh > flat_result.max_speed_kmh
    
    def test_lower_friction_reduces_speed(self):
        """Lower friction reduces cornering speed."""
        calc = CornerSpeedCalculator()
        
        # High grip
        high_grip = calc.compute_max_speed(
            radius_m=50.0,
            friction_coefficient=1.2,
            banking_deg=0.0,
            segment_id=1
        )
        
        # Low grip
        low_grip = calc.compute_max_speed(
            radius_m=50.0,
            friction_coefficient=0.8,
            banking_deg=0.0,
            segment_id=1
        )
        
        assert low_grip.max_speed_kmh < high_grip.max_speed_kmh
    
    def test_safety_margin_applied(self):
        """Safety margin is applied to calculated speed."""
        config = CornerSpeedConfig(safety_margin=0.2)  # 20% margin
        calc = CornerSpeedCalculator(config)
        
        result = calc.compute_max_speed(
            radius_m=50.0,
            friction_coefficient=1.0,
            banking_deg=0.0,
            segment_id=1
        )
        
        # Calculate theoretical max without margin
        # v = sqrt(g * μ * r)
        theoretical_mps = math.sqrt(9.81 * 1.0 * 50.0)
        theoretical_kmh = theoretical_mps * 3.6
        
        # Result should be ~80% of theoretical
        assert result.max_speed_kmh < theoretical_kmh
        assert result.max_speed_kmh > theoretical_kmh * 0.7


class TestBrakingCalculator:
    """Tests for braking calculations."""
    
    def test_braking_distance_physics(self):
        """Braking distance follows physics."""
        calc = BrakingCalculator()
        
        result = calc.compute_brake_point(
            entry_speed_kmh=200.0,
            target_speed_kmh=100.0,
            friction_coefficient=1.0,
            slope_deg=0.0
        )
        
        # Should have positive braking distance
        assert result.minimum_brake_distance_m > 0
    
    def test_higher_speed_needs_more_distance(self):
        """Higher entry speed needs more braking distance."""
        calc = BrakingCalculator()
        
        slow_result = calc.compute_brake_point(
            entry_speed_kmh=150.0,
            target_speed_kmh=80.0,
            friction_coefficient=1.0,
            slope_deg=0.0
        )
        
        fast_result = calc.compute_brake_point(
            entry_speed_kmh=200.0,
            target_speed_kmh=80.0,
            friction_coefficient=1.0,
            slope_deg=0.0
        )
        
        assert fast_result.minimum_brake_distance_m > slow_result.minimum_brake_distance_m
    
    def test_lower_friction_needs_more_distance(self):
        """Lower friction needs more braking distance."""
        calc = BrakingCalculator()
        
        high_grip = calc.compute_brake_point(
            entry_speed_kmh=180.0,
            target_speed_kmh=80.0,
            friction_coefficient=1.2,
            slope_deg=0.0
        )
        
        low_grip = calc.compute_brake_point(
            entry_speed_kmh=180.0,
            target_speed_kmh=80.0,
            friction_coefficient=0.8,
            slope_deg=0.0
        )
        
        assert low_grip.minimum_brake_distance_m > high_grip.minimum_brake_distance_m
    
    def test_downhill_needs_more_distance(self):
        """Downhill braking needs more distance."""
        calc = BrakingCalculator()
        
        flat_result = calc.compute_brake_point(
            entry_speed_kmh=180.0,
            target_speed_kmh=80.0,
            friction_coefficient=1.0,
            slope_deg=0.0
        )
        
        downhill_result = calc.compute_brake_point(
            entry_speed_kmh=180.0,
            target_speed_kmh=80.0,
            friction_coefficient=1.0,
            slope_deg=-5.0  # 5% downhill
        )
        
        assert downhill_result.minimum_brake_distance_m > flat_result.minimum_brake_distance_m
    
    def test_reaction_time_adds_distance(self):
        """Reaction time adds to braking distance."""
        config_no_reaction = BrakingConfig(reaction_time_s=0.0)
        config_with_reaction = BrakingConfig(reaction_time_s=0.5)
        
        calc_no = BrakingCalculator(config_no_reaction)
        calc_with = BrakingCalculator(config_with_reaction)
        
        result_no = calc_no.compute_brake_point(
            entry_speed_kmh=180.0,
            target_speed_kmh=80.0,
            friction_coefficient=1.0,
            slope_deg=0.0
        )
        
        result_with = calc_with.compute_brake_point(
            entry_speed_kmh=180.0,
            target_speed_kmh=80.0,
            friction_coefficient=1.0,
            slope_deg=0.0
        )
        
        # With reaction time should need more distance
        assert result_with.minimum_brake_distance_m > result_no.minimum_brake_distance_m


class TestPhysicsIntegration:
    """Integration tests for physics calculations."""
    
    def test_corner_speed_and_braking_consistent(self):
        """Corner speed and braking calculations are consistent."""
        corner_calc = CornerSpeedCalculator()
        brake_calc = BrakingCalculator()
        
        # Get max corner speed for a 50m radius corner
        corner_result = corner_calc.compute_max_speed(
            radius_m=50.0,
            friction_coefficient=1.0,
            banking_deg=0.0,
            segment_id=1
        )
        
        # Braking should be able to achieve this target
        brake_result = brake_calc.compute_brake_point(
            entry_speed_kmh=200.0,
            target_speed_kmh=corner_result.max_speed_kmh,
            friction_coefficient=1.0,
            slope_deg=0.0
        )
        
        # Should have a valid braking envelope
        assert brake_result.minimum_brake_distance_m > 0
        assert brake_result.confidence > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
