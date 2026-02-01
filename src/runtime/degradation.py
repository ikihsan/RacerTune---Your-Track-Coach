"""
Degradation Manager
Safety-Critical Adaptive AI Race Coaching System

Manages graceful degradation of system capabilities.

SAFETY: When components fail, reduce capability rather than crash.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Set
from datetime import datetime


class DegradationLevel(Enum):
    """System degradation levels."""
    
    FULL = auto()       # All capabilities available
    REDUCED = auto()    # Some capabilities disabled
    MINIMAL = auto()    # Critical functions only
    OFFLINE = auto()    # System cannot operate safely


class ComponentStatus(Enum):
    """Individual component status."""
    
    HEALTHY = auto()
    DEGRADED = auto()
    FAILED = auto()
    UNKNOWN = auto()


@dataclass
class DegradationConfig:
    """Configuration for degradation management."""
    
    # Component importance weights
    critical_components: Set[str] = None
    important_components: Set[str] = None
    optional_components: Set[str] = None
    
    # Thresholds
    reduced_threshold: int = 1  # Any important component failed
    minimal_threshold: int = 2  # Multiple important failures
    offline_threshold: int = 1  # Any critical component failed
    
    # Recovery
    recovery_required_healthy_seconds: float = 10.0
    
    def __post_init__(self):
        if self.critical_components is None:
            self.critical_components = {"gps", "fusion_engine"}
        if self.important_components is None:
            self.important_components = {"imu", "track_model", "envelope_manager"}
        if self.optional_components is None:
            self.optional_components = {"learning", "voice_tts"}


@dataclass
class DegradationState:
    """Current degradation state."""
    
    level: DegradationLevel
    failed_components: List[str]
    degraded_components: List[str]
    available_capabilities: Set[str]
    disabled_capabilities: Set[str]
    
    @property
    def is_operational(self) -> bool:
        """Check if system is operational."""
        return self.level != DegradationLevel.OFFLINE


class DegradationManager:
    """
    Manages graceful system degradation.
    
    When components fail, the system degrades capabilities
    rather than crashing entirely. This ensures:
    - Critical safety functions remain active if possible
    - User is informed of reduced capability
    - System can recover when issues resolve
    
    DEGRADATION HIERARCHY:
    FULL -> REDUCED -> MINIMAL -> OFFLINE
    
    Each level disables more capabilities while trying to
    maintain core safety functions.
    """
    
    # Capability dependencies
    CAPABILITIES = {
        "position_tracking": {"gps", "fusion_engine"},
        "physics_envelopes": {"track_model", "envelope_manager"},
        "coaching": {"position_tracking", "physics_envelopes", "voice_tts"},
        "learning": {"position_tracking", "physics_envelopes", "learning"},
        "voice_output": {"voice_tts"},
        "recording": {"position_tracking"}
    }
    
    def __init__(self, config: Optional[DegradationConfig] = None):
        self.config = config or DegradationConfig()
        
        # Component status tracking
        self._component_status: Dict[str, ComponentStatus] = {}
        self._component_last_healthy: Dict[str, datetime] = {}
        
        # Current state
        self._current_level = DegradationLevel.FULL
        self._degradation_history: List[tuple] = []
    
    def update_component_status(
        self,
        component: str,
        status: ComponentStatus
    ) -> Optional[DegradationLevel]:
        """
        Update status of a component.
        
        Args:
            component: Component identifier
            status: New status
            
        Returns:
            New degradation level if changed
        """
        old_status = self._component_status.get(component, ComponentStatus.UNKNOWN)
        self._component_status[component] = status
        
        if status == ComponentStatus.HEALTHY:
            self._component_last_healthy[component] = datetime.now()
        
        # Recompute degradation level
        new_level = self._compute_degradation_level()
        
        if new_level != self._current_level:
            self._current_level = new_level
            self._degradation_history.append((
                datetime.now(),
                new_level,
                f"{component}: {old_status.name} -> {status.name}"
            ))
            return new_level
        
        return None
    
    def _compute_degradation_level(self) -> DegradationLevel:
        """Compute current degradation level from component status."""
        
        critical_failures = 0
        important_failures = 0
        
        for component, status in self._component_status.items():
            if status == ComponentStatus.FAILED:
                if component in self.config.critical_components:
                    critical_failures += 1
                elif component in self.config.important_components:
                    important_failures += 1
        
        # Check thresholds
        if critical_failures >= self.config.offline_threshold:
            return DegradationLevel.OFFLINE
        
        if important_failures >= self.config.minimal_threshold:
            return DegradationLevel.MINIMAL
        
        if important_failures >= self.config.reduced_threshold:
            return DegradationLevel.REDUCED
        
        return DegradationLevel.FULL
    
    def get_current_state(self) -> DegradationState:
        """Get current degradation state."""
        
        failed = [c for c, s in self._component_status.items()
                  if s == ComponentStatus.FAILED]
        degraded = [c for c, s in self._component_status.items()
                    if s == ComponentStatus.DEGRADED]
        
        available, disabled = self._compute_available_capabilities()
        
        return DegradationState(
            level=self._current_level,
            failed_components=failed,
            degraded_components=degraded,
            available_capabilities=available,
            disabled_capabilities=disabled
        )
    
    def _compute_available_capabilities(self) -> tuple:
        """Compute available and disabled capabilities."""
        
        healthy_components = {
            c for c, s in self._component_status.items()
            if s in [ComponentStatus.HEALTHY, ComponentStatus.DEGRADED]
        }
        
        available = set()
        disabled = set()
        
        for capability, required_components in self.CAPABILITIES.items():
            # Check if all required components are healthy
            # (capabilities can also depend on other capabilities)
            
            can_enable = True
            for req in required_components:
                if req in self.CAPABILITIES:
                    # Recursive capability check
                    if req not in available:
                        can_enable = False
                        break
                elif req not in healthy_components:
                    can_enable = False
                    break
            
            if can_enable:
                available.add(capability)
            else:
                disabled.add(capability)
        
        return available, disabled
    
    def is_capability_available(self, capability: str) -> bool:
        """Check if a specific capability is available."""
        available, _ = self._compute_available_capabilities()
        return capability in available
    
    @property
    def current_level(self) -> DegradationLevel:
        """Get current degradation level."""
        return self._current_level
    
    @property
    def is_operational(self) -> bool:
        """Check if system is operational."""
        return self._current_level != DegradationLevel.OFFLINE
    
    @property
    def is_full_capability(self) -> bool:
        """Check if system has full capability."""
        return self._current_level == DegradationLevel.FULL
    
    def get_recovery_actions(self) -> List[str]:
        """Get recommended actions to recover from degradation."""
        
        actions = []
        
        for component, status in self._component_status.items():
            if status == ComponentStatus.FAILED:
                if component in self.config.critical_components:
                    actions.append(f"CRITICAL: Restore {component}")
                elif component in self.config.important_components:
                    actions.append(f"Restore {component}")
        
        if self._current_level == DegradationLevel.OFFLINE:
            actions.insert(0, "System offline - stop and investigate")
        
        return actions
    
    def get_history(self) -> List[tuple]:
        """Get degradation history."""
        return list(self._degradation_history)
    
    def reset(self) -> None:
        """Reset degradation state."""
        self._component_status.clear()
        self._component_last_healthy.clear()
        self._current_level = DegradationLevel.FULL
        self._degradation_history.clear()
