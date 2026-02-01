"""
Decay Manager
Safety-Critical Adaptive AI Race Coaching System

Manages decay of learned data when conditions change.

SAFETY PRINCIPLE: Learned data from different conditions is dangerous.
When conditions change, learned data must decay toward physics-only.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, Set
from datetime import datetime, timedelta

from .segment_stats import SegmentStatsStore


class DecayTrigger(Enum):
    """Triggers that cause learning decay."""
    
    NONE = auto()
    
    # Environment changes
    WEATHER_CHANGE = auto()
    TEMPERATURE_CHANGE = auto()
    SURFACE_CHANGE = auto()
    
    # Session changes
    NEW_SESSION = auto()
    LONG_BREAK = auto()
    
    # Vehicle changes
    TIRE_CHANGE = auto()
    VEHICLE_CHANGE = auto()
    
    # Manual
    MANUAL_RESET = auto()
    
    # Age-based
    DATA_AGE = auto()


@dataclass
class DecayConfig:
    """Configuration for learning decay."""
    
    # Time-based decay
    max_data_age_hours: float = 24.0
    half_life_hours: float = 8.0
    
    # Session break decay
    session_break_threshold_minutes: float = 60.0
    session_break_decay_factor: float = 0.5
    
    # Condition change factors
    weather_change_decay: float = 0.0   # Complete reset
    temperature_change_per_10c: float = 0.2
    surface_change_decay: float = 0.0   # Complete reset
    
    # Vehicle changes
    tire_change_decay: float = 0.3  # 70% retained
    vehicle_change_decay: float = 0.0  # Complete reset
    
    # Minimum retained (prevents complete zeroing from age alone)
    min_decay_factor: float = 0.1


@dataclass
class ConditionState:
    """Current environmental and vehicle conditions."""
    
    # Weather
    is_dry: bool = True
    ambient_temp_c: float = 20.0
    track_temp_c: float = 30.0
    
    # Surface
    surface_type: str = "asphalt"
    surface_condition: str = "normal"
    
    # Vehicle
    tire_compound: str = "street"
    vehicle_id: str = ""
    
    # Timing
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.now()


class DecayManager:
    """
    Manages decay of learned data based on conditions.
    
    Learned behavior is only valid under similar conditions.
    When conditions change, learned influence must decrease
    to prevent dangerous advice based on outdated data.
    
    SAFETY PRINCIPLE:
    - Dry condition data is dangerous in wet conditions
    - Old data may not reflect current grip
    - Different tires = different physics
    """
    
    def __init__(
        self,
        config: Optional[DecayConfig] = None,
        stats_store: Optional[SegmentStatsStore] = None
    ):
        self.config = config or DecayConfig()
        self.stats = stats_store
        
        self._previous_conditions: Optional[ConditionState] = None
        self._decay_history: Dict[DecayTrigger, datetime] = {}
    
    def update_conditions(
        self,
        current_conditions: ConditionState
    ) -> Dict[DecayTrigger, float]:
        """
        Update conditions and compute any required decay.
        
        Args:
            current_conditions: Current environmental/vehicle state
            
        Returns:
            Dict of triggered decays and their factors
        """
        triggered_decays: Dict[DecayTrigger, float] = {}
        
        if self._previous_conditions is None:
            self._previous_conditions = current_conditions
            return triggered_decays
        
        prev = self._previous_conditions
        
        # Check weather change
        if current_conditions.is_dry != prev.is_dry:
            triggered_decays[DecayTrigger.WEATHER_CHANGE] = self.config.weather_change_decay
        
        # Check temperature change
        temp_delta = abs(current_conditions.track_temp_c - prev.track_temp_c)
        if temp_delta >= 10.0:
            decay_amount = (temp_delta // 10) * self.config.temperature_change_per_10c
            decay_factor = max(0.0, 1.0 - decay_amount)
            triggered_decays[DecayTrigger.TEMPERATURE_CHANGE] = decay_factor
        
        # Check surface change
        if (current_conditions.surface_type != prev.surface_type or
            current_conditions.surface_condition != prev.surface_condition):
            triggered_decays[DecayTrigger.SURFACE_CHANGE] = self.config.surface_change_decay
        
        # Check session break
        if prev.last_activity:
            break_duration = current_conditions.last_activity - prev.last_activity
            if break_duration > timedelta(minutes=self.config.session_break_threshold_minutes):
                triggered_decays[DecayTrigger.LONG_BREAK] = self.config.session_break_decay_factor
        
        # Check tire change
        if current_conditions.tire_compound != prev.tire_compound:
            triggered_decays[DecayTrigger.TIRE_CHANGE] = self.config.tire_change_decay
        
        # Check vehicle change
        if (current_conditions.vehicle_id and prev.vehicle_id and
            current_conditions.vehicle_id != prev.vehicle_id):
            triggered_decays[DecayTrigger.VEHICLE_CHANGE] = self.config.vehicle_change_decay
        
        # Apply decays to stats store
        if triggered_decays and self.stats:
            combined_factor = self._combine_decay_factors(triggered_decays)
            self.stats.apply_global_decay(combined_factor)
        
        # Update history
        for trigger in triggered_decays:
            self._decay_history[trigger] = datetime.now()
        
        self._previous_conditions = current_conditions
        
        return triggered_decays
    
    def apply_age_decay(self) -> Optional[float]:
        """
        Apply time-based decay to all learned data.
        
        Returns:
            New decay factor (if applied)
        """
        if not self._previous_conditions or not self.stats:
            return None
        
        age = datetime.now() - self._previous_conditions.last_activity
        age_hours = age.total_seconds() / 3600.0
        
        if age_hours > self.config.max_data_age_hours:
            # Data too old, minimum retention
            decay_factor = self.config.min_decay_factor
        else:
            # Exponential decay based on half-life
            import math
            decay_factor = math.pow(0.5, age_hours / self.config.half_life_hours)
            decay_factor = max(decay_factor, self.config.min_decay_factor)
        
        self.stats.apply_global_decay(decay_factor)
        self._decay_history[DecayTrigger.DATA_AGE] = datetime.now()
        
        return decay_factor
    
    def reset_all_learning(self, reason: str = "manual") -> None:
        """
        Reset all learned data.
        
        Use sparingly - this discards all learning progress.
        """
        if self.stats:
            self.stats.apply_global_decay(0.0)
        
        self._decay_history[DecayTrigger.MANUAL_RESET] = datetime.now()
    
    def reset_segment_learning(self, segment_id: int, reason: str = "manual") -> None:
        """Reset learning for a specific segment."""
        if self.stats:
            self.stats.apply_decay(segment_id, 0.0)
    
    def _combine_decay_factors(self, decays: Dict[DecayTrigger, float]) -> float:
        """
        Combine multiple decay factors.
        
        Uses multiplication (most conservative combination).
        """
        if not decays:
            return 1.0
        
        combined = 1.0
        for factor in decays.values():
            combined *= factor
        
        return max(combined, self.config.min_decay_factor)
    
    def get_decay_history(self) -> Dict[DecayTrigger, datetime]:
        """Get history of decay triggers."""
        return dict(self._decay_history)
    
    def get_recommended_action(self, trigger: DecayTrigger) -> str:
        """Get recommended action for a decay trigger."""
        
        recommendations = {
            DecayTrigger.WEATHER_CHANGE: "Drive 3+ clean laps to rebuild confidence",
            DecayTrigger.TEMPERATURE_CHANGE: "Monitor grip levels for 2-3 laps",
            DecayTrigger.SURFACE_CHANGE: "Start fresh - previous data not applicable",
            DecayTrigger.LONG_BREAK: "Take 1-2 warmup laps before pushing",
            DecayTrigger.TIRE_CHANGE: "New tires need 3+ laps to learn",
            DecayTrigger.VEHICLE_CHANGE: "Complete relearning required",
            DecayTrigger.DATA_AGE: "Recent data preferred - consider relearning"
        }
        
        return recommendations.get(trigger, "Continue normal operation")
