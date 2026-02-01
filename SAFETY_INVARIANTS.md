# Safety Invariants Specification

## Document Classification: SAFETY-CRITICAL

All developers, reviewers, and maintainers **must** read and understand this document before modifying any code.

---

## 1. Absolute Safety Invariants

These invariants are **non-negotiable**. Any code that violates these must be rejected.

### S1: Silence Over Incorrect Advice

**Statement:** The system shall prefer silence over any advice that has not been validated with high confidence.

**Rationale:** Incorrect advice during high-speed driving can cause accidents. A silent system is always safer than a misleading one.

**Enforcement:**
- All voice output requires minimum confidence threshold (default: 0.85)
- Voice arbitration engine defaults to SUPPRESS
- Any uncertainty propagates as silence

**Test Criteria:**
```python
def test_low_confidence_produces_silence():
    result = voice_arbitration.decide(confidence=0.5, message="Brake now")
    assert result.action == VoiceAction.SUPPRESS
```

---

### S2: Physics Envelopes Are Hard Ceilings

**Statement:** Computed physics envelopes represent maximum controllable limits. No learned value, user input, or optimization may exceed these limits.

**Rationale:** Physics cannot be negotiated. Tire grip, vehicle dynamics, and human reaction times have fundamental limits.

**Enforcement:**
- `PhysicsEnvelope` class uses immutable ceiling values
- All `blend()` operations clamp to physics ceiling
- No API allows setting values above ceiling

**Test Criteria:**
```python
def test_learned_value_cannot_exceed_physics():
    physics_limit = 120.0  # km/h
    learned_value = 150.0  # km/h (erroneously high)
    result = envelope.blend(physics_limit, learned_value)
    assert result <= physics_limit
```

---

### S3: Learning May Only Reduce Conservatism

**Statement:** Adaptive learning (AER) may only adjust estimates downward from physics limits, never upward beyond them.

**Rationale:** Learning from real data should increase precision, not increase risk.

**Enforcement:**
- AER blend formula: `final = min(physics_ceiling, blend(conservative_default, learned))`
- Learning cannot create new ceiling values
- All learning is clamped before storage

**Test Criteria:**
```python
def test_aer_blend_respects_ceiling():
    ceiling = 100.0
    conservative = 80.0
    learned = 95.0  # Good driver achieves more
    result = aer.blend(ceiling, conservative, learned)
    assert conservative <= result <= ceiling
```

---

### S4: No Real-Time ML in Safety-Critical Loops

**Statement:** Machine learning inference, training, or model updates shall not occur in real-time safety-critical computation paths.

**Rationale:** ML systems have unpredictable latency, can produce unexpected outputs, and are difficult to formally verify.

**Enforcement:**
- Telemetry loop uses only deterministic algorithms
- Physics computation uses closed-form equations
- Learning updates occur only post-lap, offline

**Test Criteria:**
```python
def test_telemetry_loop_is_deterministic():
    loop = TelemetryLoop()
    assert not loop.uses_ml_inference()
    assert loop.max_latency_ms() < 10  # Bounded latency
```

---

### S5: Voice Output Is Deterministic and Finite

**Statement:** All voice output shall be selected from a fixed, pre-approved phrase dictionary. No dynamic text generation.

**Rationale:** Dynamic text generation (LLMs, templates) can produce unexpected, confusing, or dangerous messages.

**Enforcement:**
- `PhraseDictionary` is immutable at runtime
- Voice output selects by key only
- No string concatenation or formatting in voice path

**Test Criteria:**
```python
def test_voice_uses_fixed_phrases():
    phrase = voice.get_phrase(PhraseKey.BRAKE_EARLIER)
    assert phrase in APPROVED_PHRASES
    assert phrase == "Brake earlier"  # Exact match
```

---

### S6: Mid-Corner Speech Is Forbidden

**Statement:** Voice output shall not occur during corner apex phase unless imminent instability is detected.

**Rationale:** Mid-corner is the highest cognitive load phase. Speech distraction can cause loss of control.

**Enforcement:**
- Corner phase detection in arbitration engine
- `APEX` phase blocks all non-critical speech
- Only `INSTABILITY_WARNING` priority overrides

**Test Criteria:**
```python
def test_no_speech_at_apex():
    context = DrivingContext(phase=CornerPhase.APEX)
    result = arbitration.decide(context, message="Good line")
    assert result.action == VoiceAction.SUPPRESS
```

---

### S7: Learning Is Local, Slow, Reversible, Confidence-Gated

**Statement:** All adaptive learning shall be:
- **Local:** Per-segment, not global model updates
- **Slow:** Requires multiple consistent observations
- **Reversible:** Can decay or reset without system restart
- **Confidence-gated:** Disabled when confidence drops below threshold

**Rationale:** Global, fast, irreversible learning can corrupt the entire system from a few bad observations.

**Enforcement:**
- `SegmentStats` stores per-segment data only
- Minimum 5 clean laps before blend weight increases
- Decay function reduces learned weight over time
- Confidence threshold disables learning entirely

**Test Criteria:**
```python
def test_learning_requires_multiple_laps():
    stats = SegmentStats(segment_id=42)
    stats.add_observation(speed=95.0)  # 1 lap
    assert stats.blend_weight() == 0.0  # Not enough data
    
    for _ in range(5):
        stats.add_observation(speed=95.0)
    assert stats.blend_weight() > 0.0  # Now usable
```

---

### S8: UI Must Never Block Safety Systems

**Statement:** User interface rendering, updates, and input handling shall never block telemetry processing, physics computation, or voice arbitration.

**Rationale:** UI hangs or slow renders must not delay safety-critical decisions.

**Enforcement:**
- Telemetry loop runs in separate high-priority thread/process
- UI receives read-only snapshots
- Voice scheduler is non-blocking with timeout

**Test Criteria:**
```python
def test_ui_does_not_block_telemetry():
    telemetry = TelemetryLoop()
    ui = UIRenderer()
    
    ui.simulate_hang(duration_ms=1000)
    latency = telemetry.measure_update_latency()
    
    assert latency < 20  # Still responsive
```

---

## 2. Violation Response

If any safety invariant is violated:

1. **Development Phase:** Code review must reject the change
2. **Testing Phase:** CI/CD must fail the build
3. **Runtime Detection:** System must degrade to silent mode
4. **Post-Incident:** Root cause analysis required before resuming development

---

## 3. Change Control

Modifications to this document require:
- Written justification with safety analysis
- Review by safety-qualified engineer
- Simulation validation of new invariant
- Version increment and changelog entry

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-02 | System Architect | Initial specification |
