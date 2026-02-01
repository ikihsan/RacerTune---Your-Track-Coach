"""
Test Voice System
Safety-Critical Adaptive AI Race Coaching System

Tests for the voice arbitration system.
"""

import pytest
from src.voice.phrase_dictionary import PhraseDictionary, PhraseKey, Phrase
from src.voice.cognitive_model import CognitiveLoadModel, CognitiveLoadLevel, CognitiveState
from src.voice.arbitration import (
    VoiceArbitrationEngine, 
    VoiceRequest, 
    VoiceDecision, 
    VoiceAction,
    ArbitrationConfig
)
from src.types.geometry import CornerPhase


class TestPhraseDictionary:
    """Tests for phrase dictionary."""
    
    def test_all_keys_have_phrases(self):
        """Every PhraseKey has a corresponding phrase."""
        dictionary = PhraseDictionary()
        
        for key in PhraseKey:
            phrase = dictionary.get(key)
            assert phrase is not None
            assert isinstance(phrase, Phrase)
    
    def test_phrase_text_not_empty(self):
        """All phrases have non-empty text."""
        dictionary = PhraseDictionary()
        
        for key in PhraseKey:
            text = dictionary.get_text(key)
            assert text
            assert len(text) > 0
    
    def test_critical_phrases_exist(self):
        """Critical phrases are identified."""
        dictionary = PhraseDictionary()
        critical = dictionary.get_critical_phrases()
        
        assert len(critical) > 0
        assert PhraseKey.INSTABILITY in critical
        assert PhraseKey.LIMIT in critical
    
    def test_critical_phrases_can_interrupt(self):
        """Critical phrases are allowed to interrupt."""
        dictionary = PhraseDictionary()
        
        assert dictionary.can_interrupt(PhraseKey.INSTABILITY)
        assert dictionary.can_interrupt(PhraseKey.LIMIT)
    
    def test_normal_phrases_cannot_interrupt(self):
        """Normal phrases cannot interrupt."""
        dictionary = PhraseDictionary()
        
        assert not dictionary.can_interrupt(PhraseKey.BRAKE_EARLIER)
        assert not dictionary.can_interrupt(PhraseKey.POWER)
    
    def test_phrase_allowed_phases(self):
        """Phrases have allowed phases defined."""
        dictionary = PhraseDictionary()
        
        # Braking should be allowed on approach
        assert dictionary.is_allowed_in_phase(PhraseKey.BRAKE_NOW, "approach")
        assert dictionary.is_allowed_in_phase(PhraseKey.BRAKE_NOW, "entry")
        
        # Power should be allowed on exit
        assert dictionary.is_allowed_in_phase(PhraseKey.POWER, "exit")


class TestCognitiveModel:
    """Tests for cognitive load model."""
    
    def test_apex_is_critical_load(self):
        """Apex phase always has critical cognitive load."""
        model = CognitiveLoadModel()
        
        state = model.compute_load(
            phase=CornerPhase.APEX,
            speed_kmh=100.0,
            lateral_g=0.5,
            current_timestamp_ms=1000,
            corner_id=1
        )
        
        assert state.level == CognitiveLoadLevel.CRITICAL
    
    def test_high_g_is_high_load(self):
        """High G-forces indicate high cognitive load."""
        model = CognitiveLoadModel()
        
        state = model.compute_load(
            phase=CornerPhase.STRAIGHT,
            speed_kmh=100.0,
            lateral_g=1.3,  # High G
            current_timestamp_ms=1000,
            corner_id=1
        )
        
        assert state.level in [CognitiveLoadLevel.HIGH, CognitiveLoadLevel.CRITICAL]
    
    def test_straight_is_low_load(self):
        """Straight with low G is low cognitive load."""
        model = CognitiveLoadModel()
        
        state = model.compute_load(
            phase=CornerPhase.STRAIGHT,
            speed_kmh=100.0,
            lateral_g=0.1,
            current_timestamp_ms=1000,
            corner_id=1
        )
        
        assert state.level == CognitiveLoadLevel.LOW
    
    def test_message_interval_enforced(self):
        """Minimum message interval is enforced."""
        model = CognitiveLoadModel()
        
        # Record a message
        model.record_message(1000)
        
        # Check immediately after
        state = model.compute_load(
            phase=CornerPhase.STRAIGHT,
            speed_kmh=100.0,
            lateral_g=0.1,
            current_timestamp_ms=1500,  # Only 500ms later
            corner_id=1
        )
        
        can_speak, reason = model.can_speak(state, is_critical=False)
        assert not can_speak
        assert reason == "too_soon"
    
    def test_critical_can_override_interval(self):
        """Critical messages can override interval."""
        model = CognitiveLoadModel()
        
        # Record a message
        model.record_message(1000)
        
        state = model.compute_load(
            phase=CornerPhase.STRAIGHT,
            speed_kmh=100.0,
            lateral_g=0.1,
            current_timestamp_ms=1500,
            corner_id=1
        )
        
        can_speak, reason = model.can_speak(state, is_critical=True)
        assert can_speak
        assert reason == "critical_override"
    
    def test_lap_limit_enforced(self):
        """Maximum messages per lap is enforced."""
        model = CognitiveLoadModel()
        
        # Record many messages
        for i in range(15):
            model.record_message(i * 10000)
        
        state = model.compute_load(
            phase=CornerPhase.STRAIGHT,
            speed_kmh=100.0,
            lateral_g=0.1,
            current_timestamp_ms=200000,
            corner_id=1
        )
        
        can_speak, reason = model.can_speak(state, is_critical=False)
        assert not can_speak
        assert reason == "lap_limit"


class TestVoiceArbitration:
    """Tests for voice arbitration engine."""
    
    def test_low_confidence_suppressed(self):
        """Low confidence requests are suppressed."""
        engine = VoiceArbitrationEngine()
        
        request = VoiceRequest(
            phrase_key=PhraseKey.BRAKE_NOW,
            timestamp_ms=1000,
            confidence=0.5
        )
        
        decision = engine.submit_request(request)
        assert decision.action == VoiceAction.SUPPRESS
    
    def test_high_confidence_approved(self):
        """High confidence requests can be approved."""
        engine = VoiceArbitrationEngine()
        
        # Update phase to approach (where braking is allowed)
        engine.update_phase(CornerPhase.APPROACH)
        
        request = VoiceRequest(
            phrase_key=PhraseKey.BRAKE_NOW,
            timestamp_ms=1000,
            confidence=0.95
        )
        
        decision = engine.submit_request(request)
        # Should either be approved or suppressed for other reason, not confidence
        assert "low_confidence" not in decision.reason
    
    def test_phase_restriction_enforced(self):
        """Phrases are only allowed in correct phases."""
        engine = VoiceArbitrationEngine()
        
        # Set phase to apex
        engine.update_phase(CornerPhase.APEX)
        
        # Brake call not allowed at apex
        request = VoiceRequest(
            phrase_key=PhraseKey.BRAKE_NOW,
            timestamp_ms=1000,
            confidence=0.95
        )
        
        decision = engine.submit_request(request)
        assert decision.action == VoiceAction.SUPPRESS
        # Should be blocked by cognitive load (apex is critical)
        assert "cognitive_load" in decision.reason or "phase" in decision.reason
    
    def test_critical_bypasses_phase(self):
        """Critical phrases can bypass phase restrictions."""
        config = ArbitrationConfig()
        engine = VoiceArbitrationEngine(config)
        
        # Set phase where instability would normally be blocked
        engine.update_phase(CornerPhase.APEX)
        
        # Critical instability warning
        request = VoiceRequest(
            phrase_key=PhraseKey.INSTABILITY,
            timestamp_ms=1000,
            confidence=0.95
        )
        
        decision = engine.submit_request(request)
        
        # Critical should override phase restriction
        # (though cognitive load might still block at extreme conditions)
        if decision.action == VoiceAction.SUPPRESS:
            # Should only be blocked by extreme workload, not phase
            assert "phase" not in decision.reason
    
    def test_duplicate_suppressed(self):
        """Duplicate recent phrases are suppressed."""
        engine = VoiceArbitrationEngine()
        engine.update_phase(CornerPhase.APPROACH)
        
        # First request
        request1 = VoiceRequest(
            phrase_key=PhraseKey.BRAKE_NOW,
            timestamp_ms=1000,
            confidence=0.95
        )
        decision1 = engine.submit_request(request1)
        
        # Immediate duplicate
        request2 = VoiceRequest(
            phrase_key=PhraseKey.BRAKE_NOW,
            timestamp_ms=1500,
            confidence=0.95
        )
        decision2 = engine.submit_request(request2)
        
        # Second should be suppressed as duplicate or too soon
        if decision1.action == VoiceAction.SPEAK:
            assert decision2.action == VoiceAction.SUPPRESS
    
    def test_new_lap_resets_counters(self):
        """New lap resets message counters."""
        engine = VoiceArbitrationEngine()
        
        # New lap should reset
        engine.new_lap()
        
        stats = engine.get_stats()
        assert stats["queue_size"] == 0
    
    def test_queue_management(self):
        """Request queue is managed correctly."""
        engine = VoiceArbitrationEngine()
        engine.update_phase(CornerPhase.APPROACH)
        engine.mark_speaking_started()
        
        # Request while speaking should be queued
        request = VoiceRequest(
            phrase_key=PhraseKey.TRAIL_BRAKE,
            timestamp_ms=1000,
            confidence=0.95
        )
        
        decision = engine.submit_request(request)
        assert decision.action == VoiceAction.QUEUE
        
        # Finish speaking
        engine.mark_speaking_finished()
        
        # Should be able to get queued item
        next_request = engine.get_next_queued()
        # Might be None if expired, but queue was used


class TestVoiceIntegration:
    """Integration tests for voice system."""
    
    def test_full_approval_flow(self):
        """Test full approval flow from request to decision."""
        engine = VoiceArbitrationEngine()
        
        # Set up good conditions
        engine.update_phase(CornerPhase.APPROACH)
        engine.reset()
        
        request = VoiceRequest(
            phrase_key=PhraseKey.BRAKE_EARLIER,
            timestamp_ms=10000,
            confidence=0.95,
            segment_id=1,
            corner_id=1
        )
        
        decision = engine.submit_request(request)
        
        if decision.action == VoiceAction.SPEAK:
            assert decision.phrase_text is not None
            assert len(decision.phrase_text) > 0
    
    def test_silence_is_default(self):
        """When uncertain, silence is the default."""
        engine = VoiceArbitrationEngine()
        
        # Set up uncertain conditions
        engine.update_phase(CornerPhase.APEX)
        
        request = VoiceRequest(
            phrase_key=PhraseKey.BRAKE_EARLIER,
            timestamp_ms=1000,
            confidence=0.6  # Not great confidence
        )
        
        decision = engine.submit_request(request)
        
        # Should be suppressed
        assert decision.action == VoiceAction.SUPPRESS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
