"""
Test Safety Invariants
Safety-Critical Adaptive AI Race Coaching System

Tests to verify safety invariants are maintained.
These tests are critical - they verify the system's safety properties.
"""

import pytest
from src.types.confidence import Confidence, ConfidenceLevel
from src.types.envelopes import PhysicsCeiling, CornerSpeedEnvelope
from src.physics.envelope_manager import EnvelopeManager
from src.learning.blend_engine import BlendEngine, BlendConfig
from src.learning.segment_stats import SegmentStatistics
from src.voice.phrase_dictionary import PhraseDictionary, PhraseKey
from src.voice.arbitration import VoiceArbitrationEngine, VoiceRequest, VoiceAction
from src.odd.boundaries import BoundaryEnforcer


class TestSafetyInvariantS1:
    """
    S1: Silence is always safer than incorrect advice.
    
    Tests that the system prefers silence when uncertain.
    """
    
    def test_low_confidence_blocks_voice(self):
        """Voice output blocked when confidence is low."""
        engine = VoiceArbitrationEngine()
        
        request = VoiceRequest(
            phrase_key=PhraseKey.BRAKE_NOW,
            timestamp_ms=1000,
            confidence=0.5  # Below threshold
        )
        
        decision = engine.submit_request(request)
        assert decision.action == VoiceAction.SUPPRESS
        assert "low_confidence" in decision.reason
    
    def test_high_confidence_allows_voice(self):
        """Voice output allowed when confidence is high."""
        engine = VoiceArbitrationEngine()
        
        request = VoiceRequest(
            phrase_key=PhraseKey.BRAKE_NOW,
            timestamp_ms=1000,
            confidence=0.95
        )
        
        decision = engine.submit_request(request)
        # Should be approved (other gates may still block, but not confidence)
        assert "low_confidence" not in decision.reason


class TestSafetyInvariantS2:
    """
    S2: Physics-based limits are computed conservatively.
    
    Tests that safety margins are applied correctly.
    """
    
    def test_boundary_enforcer_clamps_speed(self):
        """Speed values are clamped to safe range."""
        enforcer = BoundaryEnforcer()
        
        # Test clamping
        clamped = enforcer.clamp_speed(400.0)  # Above max
        assert clamped <= 300.0  # Should be clamped
    
    def test_boundary_enforcer_detects_violation(self):
        """Boundary violations are detected."""
        enforcer = BoundaryEnforcer()
        
        result = enforcer.check_speed(350.0)
        assert not result.passed
        assert result.bounded_value < result.original_value


class TestSafetyInvariantS3:
    """
    S3: Confidence gates all outputs.
    
    Tests that confidence is checked at all output points.
    """
    
    def test_confidence_level_mapping(self):
        """Confidence values map correctly to levels."""
        c = Confidence(0.9)
        assert c.level == ConfidenceLevel.HIGH
        
        c = Confidence(0.75)
        assert c.level == ConfidenceLevel.MEDIUM
        
        c = Confidence(0.5)
        assert c.level == ConfidenceLevel.LOW
        
        c = Confidence(0.3)
        assert c.level == ConfidenceLevel.VERY_LOW
    
    def test_confidence_floor_check(self):
        """Confidence floor is enforced."""
        enforcer = BoundaryEnforcer()
        
        result = enforcer.check_confidence(0.5, for_advice=True)
        assert not result.passed


class TestSafetyInvariantS4:
    """
    S4: Physics models are hard ceilings.
    
    Tests that physics ceilings cannot be exceeded by learning.
    """
    
    def test_physics_ceiling_is_immutable(self):
        """PhysicsCeiling is immutable."""
        ceiling = PhysicsCeiling(
            max_speed_kmh=150.0,
            max_deceleration_g=1.2,
            max_lateral_g=1.0
        )
        
        # Attempting to modify should fail
        with pytest.raises(Exception):  # frozen dataclass
            ceiling.max_speed_kmh = 200.0
    
    def test_blend_engine_respects_physics(self):
        """Blend engine never exceeds physics ceiling."""
        blend = BlendEngine(BlendConfig(max_learned_influence=0.3))
        
        # Create physics envelope
        physics = CornerSpeedEnvelope(
            segment_id=1,
            max_speed_kmh=100.0,
            min_speed_kmh=50.0,
            confidence=0.95
        )
        
        # Create learned stats that exceed physics
        stats = SegmentStatistics(
            segment_id=1,
            observation_count=20,
            entry_speed_mean_kmh=120.0,  # Higher than physics!
            entry_speed_std_kmh=5.0,
            entry_speed_max_kmh=130.0,
            confidence_weighted_count=18.0
        )
        
        result = blend.blend_corner_speed(physics, stats)
        
        # Blended value must not exceed physics ceiling
        assert result.blended_value <= physics.max_speed_kmh
        assert result.was_physics_limited or result.learned_value <= physics.max_speed_kmh
    
    def test_learned_influence_is_capped(self):
        """Learned data influence is capped."""
        config = BlendConfig(max_learned_influence=0.3)
        blend = BlendEngine(config)
        
        # Maximum influence should never exceed config
        assert blend.get_max_allowed_influence() <= 0.3


class TestSafetyInvariantS5:
    """
    S5: Voice output is deterministic and finite.
    
    Tests that all voice output comes from fixed dictionary.
    """
    
    def test_all_phrase_keys_have_text(self):
        """All phrase keys have corresponding text."""
        dictionary = PhraseDictionary()
        
        for key in PhraseKey:
            phrase = dictionary.get(key)
            assert phrase is not None
            assert len(phrase.text) > 0
    
    def test_phrase_text_is_speakable(self):
        """All phrases are short enough to speak quickly."""
        dictionary = PhraseDictionary()
        
        for phrase in dictionary.get_all_phrases():
            # Phrases should be 6 words or less (per Phrase validation)
            word_count = len(phrase.text.split())
            assert word_count <= 6, f"Phrase too long: {phrase.text}"
    
    def test_unknown_key_raises_error(self):
        """Requesting unknown key raises error."""
        dictionary = PhraseDictionary()
        
        with pytest.raises(KeyError):
            dictionary.get("invalid_key")


class TestSafetyInvariantS6:
    """
    S6: Mid-corner speech is forbidden unless instability imminent.
    
    Tests that apex phase blocks non-critical speech.
    """
    
    def test_apex_phase_blocks_normal_speech(self):
        """Non-critical phrases blocked during apex."""
        from src.types.geometry import CornerPhase
        from src.voice.cognitive_model import CognitiveLoadModel, CognitiveLoadLevel
        
        model = CognitiveLoadModel()
        
        # Simulate apex phase
        state = model.compute_load(
            phase=CornerPhase.APEX,
            speed_kmh=100.0,
            lateral_g=0.8,
            current_timestamp_ms=1000,
            corner_id=1
        )
        
        # Normal speech should be blocked
        can_speak, reason = model.can_speak(state, is_critical=False)
        assert not can_speak
        assert reason == "apex_phase"
    
    def test_apex_phase_allows_critical_speech(self):
        """Critical phrases allowed during apex (with restrictions)."""
        from src.types.geometry import CornerPhase
        from src.voice.cognitive_model import CognitiveLoadModel
        
        model = CognitiveLoadModel()
        
        state = model.compute_load(
            phase=CornerPhase.APEX,
            speed_kmh=100.0,
            lateral_g=0.8,  # Not extreme
            current_timestamp_ms=1000,
            corner_id=1
        )
        
        # Critical speech should be allowed
        can_speak, reason = model.can_speak(state, is_critical=True)
        assert can_speak
        assert reason == "critical_override"


class TestGripCirclePhysics:
    """Tests for friction circle physics enforcement."""
    
    def test_friction_circle_computation(self):
        """Friction circle is computed correctly."""
        from src.physics.combined_grip import FrictionCircleEnforcer
        
        enforcer = FrictionCircleEnforcer()
        
        # Test usage calculation
        usage = enforcer.compute_grip_usage(0.6, 0.8, 1.0)
        
        # sqrt(0.6^2 + 0.8^2) = 1.0, so usage should be 100% at μ=1.0
        assert abs(usage - 1.0) < 0.01
    
    def test_available_grip_calculation(self):
        """Available grip is calculated correctly."""
        from src.physics.combined_grip import FrictionCircleEnforcer
        
        enforcer = FrictionCircleEnforcer()
        
        # Using some longitudinal G, available lateral should be reduced
        available = enforcer.compute_available_lateral(0.6, 1.0)
        
        # sqrt(1.0^2 - 0.6^2) = 0.8
        assert abs(available - 0.8) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
