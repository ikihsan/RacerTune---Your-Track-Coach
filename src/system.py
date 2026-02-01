"""
Safety-Critical Adaptive AI Race Coaching System
Main System Integration

This is the top-level integration module that connects all components.

SAFETY ARCHITECTURE:
- All components follow safety invariants from SAFETY_INVARIANTS.md
- Failures are isolated and handled gracefully
- System degrades rather than crashes
- Silence is always a safe fallback
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import time

# Core types
from .types.confidence import ConfidenceTracker
from .types.telemetry import TelemetryFrame, LapData
from .types.geometry import TrackModel, CornerPhase
from .types.envelopes import SegmentEnvelope

# Sensors
from .sensors.gps_processor import GPSProcessor
from .sensors.imu_processor import IMUProcessor
from .sensors.fusion_engine import SensorFusionEngine
from .sensors.disagreement import DisagreementDetector

# Track
from .track.driven_laps import DrivenLapProcessor
from .track.geometry_builder import TrackGeometryBuilder

# Physics
from .physics.corner_speed import CornerSpeedCalculator
from .physics.braking_envelope import BrakingCalculator
from .physics.combined_grip import FrictionCircleEnforcer
from .physics.envelope_manager import EnvelopeManager

# Learning
from .learning.segment_stats import SegmentStatsStore
from .learning.lap_validator import LapValidator
from .learning.blend_engine import BlendEngine
from .learning.decay_manager import DecayManager

# Prediction
from .prediction.entry_speed import EntrySpeedDetector
from .prediction.braking_point import BrakingPointDetector
from .prediction.steering_intensity import SteeringIntensityDetector
from .prediction.flag_arbiter import FlagArbiter

# Voice
from .voice.phrase_dictionary import PhraseDictionary
from .voice.cognitive_model import CognitiveLoadModel
from .voice.arbitration import VoiceArbitrationEngine, VoiceRequest

# Runtime
from .runtime.main_loop import MainLoop
from .runtime.mode_controller import ModeController, OperatingMode
from .runtime.degradation import DegradationManager, ComponentStatus

# ODD
from .odd.validator import ODDValidator, CurrentConditions
from .odd.conditions import ConditionMonitor
from .odd.boundaries import BoundaryEnforcer


@dataclass
class SystemConfig:
    """Top-level system configuration."""
    
    # Target update rate
    target_hz: int = 50
    
    # Feature flags
    enable_voice: bool = True
    enable_learning: bool = True
    enable_coaching: bool = True
    
    # Safety thresholds
    min_confidence_for_operation: float = 0.7
    min_confidence_for_coaching: float = 0.85


class CoachingSystem:
    """
    Main coaching system integration.
    
    This class integrates all components into a functioning
    coaching system. It is responsible for:
    - Initializing all components
    - Managing data flow between components
    - Handling the main loop
    - Ensuring safety invariants are maintained
    
    SAFETY INVARIANTS (from SAFETY_INVARIANTS.md):
    S1: Silence is always safer than incorrect advice
    S2: Physics-based limits are computed conservatively
    S3: Confidence gates all outputs
    S4: Physics models are hard ceilings
    S5: Voice output is deterministic and finite
    S6: Mid-corner speech is forbidden (unless critical)
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        self.config = config or SystemConfig()
        
        # Initialize all components
        self._init_sensors()
        self._init_track()
        self._init_physics()
        self._init_learning()
        self._init_prediction()
        self._init_voice()
        self._init_runtime()
        self._init_odd()
        
        # State
        self._is_initialized = False
        self._current_lap: Optional[LapData] = None
        self._track_model: Optional[TrackModel] = None
    
    def _init_sensors(self) -> None:
        """Initialize sensor components."""
        self.gps_processor = GPSProcessor()
        self.imu_processor = IMUProcessor()
        self.fusion_engine = SensorFusionEngine()
        self.disagreement_detector = DisagreementDetector()
    
    def _init_track(self) -> None:
        """Initialize track components."""
        self.lap_processor = DrivenLapProcessor()
        self.geometry_builder = TrackGeometryBuilder()
    
    def _init_physics(self) -> None:
        """Initialize physics components."""
        self.corner_speed_calc = CornerSpeedCalculator()
        self.braking_calc = BrakingCalculator()
        self.friction_circle = FrictionCircleEnforcer()
        self.envelope_manager = EnvelopeManager()
    
    def _init_learning(self) -> None:
        """Initialize learning components."""
        self.stats_store = SegmentStatsStore()
        self.lap_validator = LapValidator()
        self.blend_engine = BlendEngine()
        self.decay_manager = DecayManager(stats_store=self.stats_store)
    
    def _init_prediction(self) -> None:
        """Initialize prediction components."""
        self.entry_speed_detector = EntrySpeedDetector()
        self.braking_detector = BrakingPointDetector()
        self.steering_detector = SteeringIntensityDetector()
        self.flag_arbiter = FlagArbiter()
    
    def _init_voice(self) -> None:
        """Initialize voice components."""
        self.phrase_dict = PhraseDictionary()
        self.cognitive_model = CognitiveLoadModel()
        self.voice_arbitration = VoiceArbitrationEngine(
            phrase_dictionary=self.phrase_dict,
            cognitive_model=self.cognitive_model
        )
    
    def _init_runtime(self) -> None:
        """Initialize runtime components."""
        self.main_loop = MainLoop()
        self.mode_controller = ModeController()
        self.degradation_manager = DegradationManager()
        self.confidence_tracker = ConfidenceTracker()
    
    def _init_odd(self) -> None:
        """Initialize ODD components."""
        self.odd_validator = ODDValidator()
        self.condition_monitor = ConditionMonitor()
        self.boundary_enforcer = BoundaryEnforcer()
    
    def initialize(self) -> bool:
        """
        Initialize the system.
        
        Returns:
            True if initialization successful
        """
        try:
            # Validate all components
            self._validate_components()
            
            # Register main loop callbacks
            self.main_loop.register_callbacks(
                on_sensor_read=self._on_sensor_read,
                on_fusion=self._on_fusion,
                on_detection=self._on_detection,
                on_voice=self._on_voice,
                on_log=self._on_log,
                on_error=self._on_error
            )
            
            # Initialize main loop
            if not self.main_loop.initialize():
                return False
            
            self._is_initialized = True
            return True
            
        except Exception as e:
            print(f"Initialization failed: {e}")
            return False
    
    def _validate_components(self) -> None:
        """Validate all components are ready."""
        # Each component should have a validation method
        # For now, just ensure they exist
        required_components = [
            self.gps_processor,
            self.fusion_engine,
            self.envelope_manager,
            self.voice_arbitration,
            self.odd_validator,
            self.boundary_enforcer
        ]
        
        for component in required_components:
            if component is None:
                raise RuntimeError("Required component not initialized")
    
    def process_frame(self, frame: TelemetryFrame) -> Dict[str, Any]:
        """
        Process a single telemetry frame.
        
        Args:
            frame: Telemetry frame from sensors
            
        Returns:
            Processing result with any voice output
        """
        if not self._is_initialized:
            return {"error": "System not initialized"}
        
        return self.main_loop.run_single_iteration(frame.timestamp_ms)
    
    def _on_sensor_read(self, timestamp_ms: int) -> None:
        """Callback for sensor read phase."""
        # In a real system, this would read from actual sensors
        pass
    
    def _on_fusion(self, timestamp_ms: int) -> None:
        """Callback for fusion phase."""
        # Fuse sensor data
        pass
    
    def _on_detection(self, timestamp_ms: int) -> None:
        """Callback for detection phase."""
        # Run detection algorithms
        pass
    
    def _on_voice(self, timestamp_ms: int) -> None:
        """Callback for voice phase."""
        # Arbitrate and output voice
        pass
    
    def _on_log(self, timestamp_ms: int) -> None:
        """Callback for logging phase."""
        # Log telemetry
        pass
    
    def _on_error(self, error: Exception) -> None:
        """Callback for error handling."""
        print(f"System error: {error}")
    
    def load_track(self, track_model: TrackModel) -> None:
        """Load a track model."""
        self._track_model = track_model
        self.envelope_manager.build_envelopes(track_model)
    
    def start_lap(self) -> None:
        """Start recording a new lap."""
        self._current_lap = LapData(lap_number=1, frames=[])
        self.voice_arbitration.new_lap()
        self.flag_arbiter.new_lap()
    
    def end_lap(self) -> None:
        """End current lap and process for learning."""
        if self._current_lap is None:
            return
        
        # Validate lap for learning
        validation = self.lap_validator.validate_lap(self._current_lap)
        
        if validation.is_valid and self.mode_controller.learning_enabled:
            # Process lap for learning
            pass
        
        self._current_lap = None
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            "initialized": self._is_initialized,
            "mode": self.mode_controller.current_mode.name,
            "voice_enabled": self.mode_controller.voice_enabled,
            "learning_enabled": self.mode_controller.learning_enabled,
            "degradation_level": self.degradation_manager.current_level.name,
            "has_track": self._track_model is not None,
            "loop_metrics": {
                "count": self.main_loop.metrics.loop_count,
                "avg_time_ms": self.main_loop.metrics.avg_time_ms,
                "overruns": self.main_loop.metrics.overrun_count
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown the system."""
        self.main_loop.shutdown()
        self._is_initialized = False


# Singleton instance for easy access
_system_instance: Optional[CoachingSystem] = None


def get_system() -> CoachingSystem:
    """Get or create the system instance."""
    global _system_instance
    if _system_instance is None:
        _system_instance = CoachingSystem()
    return _system_instance


def initialize_system(config: Optional[SystemConfig] = None) -> bool:
    """Initialize the coaching system."""
    global _system_instance
    _system_instance = CoachingSystem(config)
    return _system_instance.initialize()
