# Safety-Critical Adaptive AI Race Coaching System

## Master Engineering Specification v1.0

**Classification:** Safety-Critical System  
**Revision Date:** 2026-02-02  
**Governing Principle:** Trust over Performance — Always

---

## 1. System Purpose

A closed-circuit, driver-assist AI coaching system that:
- Builds accurate custom track geometry using multi-source fusion
- Computes controllable performance envelopes (speed, braking, steering)
- Provides minimal, voice-only, race-engineer-style guidance
- Improves accuracy gradually using real lap data
- **Never exceeds physics limits**
- **Never pressures the driver**
- **Fails silent rather than giving incorrect advice**

This system **advises only**. It never controls the vehicle. It never replaces the driver.

---

## 2. Absolute Safety Invariants

These are **hard laws** that cannot be violated:

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| S1 | Silence is always safer than incorrect advice | Voice arbitration default-deny |
| S2 | Physics envelopes are hard ceilings | Clamping in envelope computation |
| S3 | Learned values may only reduce conservatism, never exceed physics | AER blend validation |
| S4 | No real-time machine learning in safety-critical loops | Architecture separation |
| S5 | Voice output must be deterministic and finite | Fixed phrase dictionary |
| S6 | Mid-corner speech is forbidden unless instability imminent | Phase-gated arbitration |
| S7 | All learning must be local, slow, reversible, confidence-gated | AER module design |
| S8 | UI must never block telemetry, physics, or voice | Non-blocking architecture |

**If any invariant is violated → redesign the system.**

---

## 3. Project Structure

```
f1/
├── README.md                    # This file
├── SAFETY_INVARIANTS.md         # Formal safety requirements
├── requirements.txt             # Python dependencies
├── config/
│   ├── odd_definition.yaml      # Operational Design Domain
│   ├── physics_constants.yaml   # Vehicle physics parameters
│   └── voice_phrases.yaml       # Fixed phrase dictionary
├── src/
│   ├── __init__.py
│   ├── types/                   # Core type definitions
│   │   ├── __init__.py
│   │   ├── geometry.py          # Track geometry types
│   │   ├── telemetry.py         # Sensor data types
│   │   ├── envelopes.py         # Physics envelope types
│   │   └── confidence.py        # Confidence scoring types
│   ├── sensors/                 # Sensor fusion module
│   │   ├── __init__.py
│   │   ├── gps_processor.py     # GPS noise modeling
│   │   ├── imu_processor.py     # IMU drift correction
│   │   ├── fusion_engine.py     # Confidence-weighted fusion
│   │   └── disagreement.py      # Sensor disagreement detection
│   ├── track/                   # Track geometry reconstruction
│   │   ├── __init__.py
│   │   ├── driven_laps.py       # Method 1: GPS lap averaging
│   │   ├── satellite_anchor.py  # Method 2: Map reference
│   │   ├── imu_curvature.py     # Method 3: IMU local curvature
│   │   ├── edge_detection.py    # Optional: Track width estimation
│   │   └── geometry_builder.py  # Final track model assembly
│   ├── physics/                 # Physics envelope computation
│   │   ├── __init__.py
│   │   ├── tire_model.py        # Simplified tire grip model
│   │   ├── corner_speed.py      # Maximum controllable speed
│   │   ├── braking_envelope.py  # Deceleration limits
│   │   ├── steering_envelope.py # Steering intensity limits
│   │   └── combined_grip.py     # Friction circle enforcement
│   ├── learning/                # Adaptive Envelope Refinement
│   │   ├── __init__.py
│   │   ├── segment_stats.py     # Per-segment statistics
│   │   ├── lap_validator.py     # Clean lap detection
│   │   ├── blend_engine.py      # Conservative blending
│   │   └── decay_manager.py     # Condition-based decay
│   ├── prediction/              # Deviation detection
│   │   ├── __init__.py
│   │   ├── entry_speed.py       # Entry too fast detection
│   │   ├── steering_intensity.py# Aggressive steering detection
│   │   ├── braking_point.py     # Late braking detection
│   │   └── flag_arbiter.py      # Symbolic flag output
│   ├── voice/                   # Voice coaching system
│   │   ├── __init__.py
│   │   ├── phrase_dictionary.py # Fixed phrases only
│   │   ├── cognitive_model.py   # Driver attention model
│   │   ├── arbitration.py       # Voice arbitration engine
│   │   └── tts_interface.py     # Text-to-speech wrapper
│   ├── runtime/                 # Real-time architecture
│   │   ├── __init__.py
│   │   ├── telemetry_loop.py    # High-priority telemetry
│   │   ├── physics_loop.py      # Physics computation
│   │   ├── voice_scheduler.py   # Non-blocking voice
│   │   └── failure_isolator.py  # Failure containment
│   ├── analysis/                # Post-lap analysis
│   │   ├── __init__.py
│   │   ├── track_overlay.py     # Track map visualization
│   │   ├── envelope_comparison.py# Speed vs envelope
│   │   ├── heatmaps.py          # Steering intensity maps
│   │   └── summary_generator.py # Post-lap voice summary
│   └── odd/                     # Operational Design Domain
│       ├── __init__.py
│       ├── domain_enforcer.py   # ODD boundary detection
│       └── degradation.py       # Graceful degradation
└── tests/
    ├── __init__.py
    ├── test_safety_invariants.py
    ├── test_sensor_fusion.py
    ├── test_physics_envelopes.py
    └── test_voice_arbitration.py
```

---

## 4. Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with default configuration
python -m src.runtime.main --config config/odd_definition.yaml

# Run post-lap analysis
python -m src.analysis.main --lap-file recorded_lap.json
```

---

## 5. Governing Principle

> This system must behave like a responsible human race engineer,
> not an optimizer, not an AI assistant, not a coach pushing limits.
>
> **If forced to choose between Performance and Trust → Always choose Trust.**

---

## License

Proprietary — Safety-Critical System — Not for public distribution without review.
