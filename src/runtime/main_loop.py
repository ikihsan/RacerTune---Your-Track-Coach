"""
Main Loop
Safety-Critical Adaptive AI Race Coaching System

Core runtime loop with real-time scheduling.

SAFETY: Deterministic timing, isolated failure modes.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable, List, Dict, Any
import time


class RuntimeState(Enum):
    """Runtime system states."""
    
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    DEGRADED = auto()
    PAUSED = auto()
    SHUTDOWN = auto()


@dataclass
class LoopConfig:
    """Configuration for main loop."""
    
    # Target loop frequency
    target_hz: int = 50  # 50 Hz = 20ms per loop
    
    # Timing constraints
    max_loop_time_ms: float = 15.0  # Must complete in 15ms
    warning_loop_time_ms: float = 10.0  # Warn if over 10ms
    
    # Watchdog
    watchdog_timeout_ms: float = 100.0  # If no loop for 100ms, alarm
    
    # Error handling
    max_consecutive_errors: int = 3
    error_recovery_delay_ms: float = 50.0


@dataclass
class LoopMetrics:
    """Metrics for monitoring loop performance."""
    
    loop_count: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    
    overrun_count: int = 0
    error_count: int = 0
    
    last_loop_time_ms: float = 0.0
    last_loop_timestamp_ms: int = 0


class MainLoop:
    """
    Main runtime loop for the coaching system.
    
    Executes all system components in a deterministic order:
    1. Read sensors
    2. Fuse data
    3. Update position/phase
    4. Run detection
    5. Arbitrate voice
    6. Output voice (if any)
    7. Log telemetry
    
    SAFETY PRINCIPLES:
    - Fixed execution order
    - Deterministic timing
    - Isolated failures (one component failing doesn't crash others)
    - Graceful degradation
    """
    
    def __init__(self, config: Optional[LoopConfig] = None):
        self.config = config or LoopConfig()
        
        # State
        self._state = RuntimeState.INITIALIZING
        self._metrics = LoopMetrics()
        
        # Callbacks
        self._on_sensor_read: Optional[Callable] = None
        self._on_fusion: Optional[Callable] = None
        self._on_detection: Optional[Callable] = None
        self._on_voice: Optional[Callable] = None
        self._on_log: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
        
        # Error tracking
        self._consecutive_errors = 0
        self._last_error: Optional[Exception] = None
    
    def register_callbacks(
        self,
        on_sensor_read: Optional[Callable] = None,
        on_fusion: Optional[Callable] = None,
        on_detection: Optional[Callable] = None,
        on_voice: Optional[Callable] = None,
        on_log: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ) -> None:
        """Register callback functions for each loop phase."""
        self._on_sensor_read = on_sensor_read
        self._on_fusion = on_fusion
        self._on_detection = on_detection
        self._on_voice = on_voice
        self._on_log = on_log
        self._on_error = on_error
    
    def initialize(self) -> bool:
        """
        Initialize the runtime.
        
        Returns:
            True if initialization successful
        """
        try:
            self._state = RuntimeState.READY
            self._metrics = LoopMetrics()
            self._consecutive_errors = 0
            return True
        except Exception as e:
            self._last_error = e
            return False
    
    def run_single_iteration(self, timestamp_ms: int) -> Dict[str, Any]:
        """
        Execute a single loop iteration.
        
        Args:
            timestamp_ms: Current timestamp
            
        Returns:
            Dict with iteration results and timing
        """
        if self._state not in [RuntimeState.RUNNING, RuntimeState.DEGRADED]:
            self._state = RuntimeState.RUNNING
        
        start_time = time.perf_counter()
        results: Dict[str, Any] = {
            "timestamp_ms": timestamp_ms,
            "phases": {}
        }
        
        try:
            # Phase 1: Read sensors
            results["phases"]["sensor"] = self._execute_phase(
                "sensor", self._on_sensor_read, timestamp_ms
            )
            
            # Phase 2: Fuse data
            results["phases"]["fusion"] = self._execute_phase(
                "fusion", self._on_fusion, timestamp_ms
            )
            
            # Phase 3: Detection
            results["phases"]["detection"] = self._execute_phase(
                "detection", self._on_detection, timestamp_ms
            )
            
            # Phase 4: Voice arbitration
            results["phases"]["voice"] = self._execute_phase(
                "voice", self._on_voice, timestamp_ms
            )
            
            # Phase 5: Logging
            results["phases"]["log"] = self._execute_phase(
                "log", self._on_log, timestamp_ms
            )
            
            # Success
            self._consecutive_errors = 0
            
        except Exception as e:
            self._handle_error(e)
            results["error"] = str(e)
        
        # Record timing
        end_time = time.perf_counter()
        loop_time_ms = (end_time - start_time) * 1000.0
        
        self._update_metrics(loop_time_ms, timestamp_ms)
        
        results["loop_time_ms"] = loop_time_ms
        results["overrun"] = loop_time_ms > self.config.max_loop_time_ms
        
        return results
    
    def _execute_phase(
        self,
        name: str,
        callback: Optional[Callable],
        timestamp_ms: int
    ) -> Dict[str, Any]:
        """Execute a single phase with isolation."""
        
        result = {
            "name": name,
            "executed": False,
            "time_ms": 0.0,
            "error": None
        }
        
        if callback is None:
            return result
        
        start = time.perf_counter()
        
        try:
            callback(timestamp_ms)
            result["executed"] = True
        except Exception as e:
            result["error"] = str(e)
            # Phase errors are isolated, don't propagate
        
        result["time_ms"] = (time.perf_counter() - start) * 1000.0
        
        return result
    
    def _handle_error(self, error: Exception) -> None:
        """Handle loop error."""
        self._consecutive_errors += 1
        self._last_error = error
        self._metrics.error_count += 1
        
        if self._on_error:
            try:
                self._on_error(error)
            except:
                pass
        
        if self._consecutive_errors >= self.config.max_consecutive_errors:
            self._state = RuntimeState.DEGRADED
    
    def _update_metrics(self, loop_time_ms: float, timestamp_ms: int) -> None:
        """Update loop metrics."""
        self._metrics.loop_count += 1
        self._metrics.total_time_ms += loop_time_ms
        self._metrics.last_loop_time_ms = loop_time_ms
        self._metrics.last_loop_timestamp_ms = timestamp_ms
        
        if loop_time_ms < self._metrics.min_time_ms:
            self._metrics.min_time_ms = loop_time_ms
        
        if loop_time_ms > self._metrics.max_time_ms:
            self._metrics.max_time_ms = loop_time_ms
        
        self._metrics.avg_time_ms = self._metrics.total_time_ms / self._metrics.loop_count
        
        if loop_time_ms > self.config.max_loop_time_ms:
            self._metrics.overrun_count += 1
    
    def pause(self) -> None:
        """Pause the runtime."""
        self._state = RuntimeState.PAUSED
    
    def resume(self) -> None:
        """Resume the runtime."""
        if self._state == RuntimeState.PAUSED:
            self._state = RuntimeState.RUNNING
    
    def shutdown(self) -> None:
        """Shutdown the runtime."""
        self._state = RuntimeState.SHUTDOWN
    
    @property
    def state(self) -> RuntimeState:
        """Get current runtime state."""
        return self._state
    
    @property
    def metrics(self) -> LoopMetrics:
        """Get loop metrics."""
        return self._metrics
    
    @property
    def is_healthy(self) -> bool:
        """Check if runtime is healthy."""
        return self._state in [RuntimeState.READY, RuntimeState.RUNNING]
    
    @property
    def last_error(self) -> Optional[Exception]:
        """Get last error (if any)."""
        return self._last_error
