"""
Friction Circle (Combined Grip) Enforcer
Safety-Critical Adaptive AI Race Coaching System

Enforces the friction circle constraint on combined longitudinal and lateral forces.

SAFETY: Total grip usage must never exceed available grip.
"""

from dataclasses import dataclass
from typing import Tuple
import math

from ..types.envelopes import CombinedGripEnvelope, PhysicsCeiling


@dataclass
class FrictionCircleConfig:
    """Configuration for friction circle enforcement."""
    
    # Grip limits
    max_grip_normalized: float = 1.0  # Normalized to 1.0
    
    # Shape factors (1.0 = circle, <1.0 = ellipse)
    longitudinal_factor: float = 1.0  # Braking/acceleration capacity
    lateral_factor: float = 1.0       # Cornering capacity
    
    # Stability margin - keep grip in reserve
    stability_margin: float = 0.15  # 15% reserve
    
    # Warning thresholds
    warning_threshold: float = 0.75   # 75% grip usage
    critical_threshold: float = 0.90  # 90% grip usage


class FrictionCircleEnforcer:
    """
    Enforces the friction circle constraint.
    
    The friction circle defines total available tire grip:
    sqrt(ax² + ay²) <= μ * g
    
    Where:
    - ax = longitudinal acceleration (braking/acceleration)
    - ay = lateral acceleration (cornering)
    - μ = friction coefficient
    - g = gravity
    
    When normalized:
    sqrt(fx² + fy²) <= 1.0
    
    Where fx and fy are fractions of maximum grip.
    
    SAFETY:
    - Monitor grip usage in real-time
    - Warn when approaching limit
    - Maintain stability margin
    """
    
    def __init__(self, config: FrictionCircleConfig = None):
        self.config = config or FrictionCircleConfig()
    
    def compute_grip_usage(
        self,
        longitudinal_g: float,
        lateral_g: float,
        max_longitudinal_g: float = 1.0,
        max_lateral_g: float = 1.2
    ) -> CombinedGripEnvelope:
        """
        Compute current grip usage.
        
        Args:
            longitudinal_g: Current longitudinal acceleration in g
            lateral_g: Current lateral acceleration in g
            max_longitudinal_g: Maximum longitudinal grip in g
            max_lateral_g: Maximum lateral grip in g
            
        Returns:
            Combined grip envelope with usage information
        """
        # Normalize to grip capacity
        fx = abs(longitudinal_g) / max_longitudinal_g
        fy = abs(lateral_g) / max_lateral_g
        
        # Apply shape factors
        fx_shaped = fx / self.config.longitudinal_factor
        fy_shaped = fy / self.config.lateral_factor
        
        # Total grip (friction circle)
        total = math.sqrt(fx_shaped**2 + fy_shaped**2)
        
        return CombinedGripEnvelope(
            max_total_grip=PhysicsCeiling(
                value=self.config.max_grip_normalized,
                unit="normalized",
                source="friction_circle"
            ),
            longitudinal_grip_used=fx,
            lateral_grip_used=fy,
            stability_margin=self.config.stability_margin
        )
    
    def check_limit(
        self,
        longitudinal_g: float,
        lateral_g: float,
        max_longitudinal_g: float = 1.0,
        max_lateral_g: float = 1.2
    ) -> Tuple[bool, str, float]:
        """
        Check if approaching or exceeding grip limit.
        
        Returns:
            Tuple of (is_at_limit, status, remaining_grip)
        """
        envelope = self.compute_grip_usage(
            longitudinal_g, lateral_g,
            max_longitudinal_g, max_lateral_g
        )
        
        total = envelope.total_grip_used
        remaining = 1.0 - total
        
        if total >= 1.0:
            return True, "EXCEEDED", remaining
        elif total >= self.config.critical_threshold:
            return True, "CRITICAL", remaining
        elif total >= self.config.warning_threshold:
            return False, "WARNING", remaining
        else:
            return False, "OK", remaining
    
    def compute_available_lateral(
        self,
        longitudinal_g: float,
        max_longitudinal_g: float = 1.0,
        max_lateral_g: float = 1.2
    ) -> float:
        """
        Compute available lateral grip given longitudinal usage.
        
        Used to determine safe cornering speed during braking.
        
        Returns:
            Available lateral acceleration in g
        """
        fx = abs(longitudinal_g) / max_longitudinal_g
        
        # Apply shape factor
        fx_shaped = fx / self.config.longitudinal_factor
        
        # Apply stability margin
        max_total = 1.0 - self.config.stability_margin
        
        if fx_shaped >= max_total:
            return 0.0
        
        # fy_max = sqrt(max² - fx²)
        fy_available = math.sqrt(max_total**2 - fx_shaped**2)
        
        # Convert back to g
        return fy_available * max_lateral_g * self.config.lateral_factor
    
    def compute_available_longitudinal(
        self,
        lateral_g: float,
        max_longitudinal_g: float = 1.0,
        max_lateral_g: float = 1.2
    ) -> float:
        """
        Compute available longitudinal grip given lateral usage.
        
        Used to determine safe braking while cornering.
        
        Returns:
            Available longitudinal acceleration in g
        """
        fy = abs(lateral_g) / max_lateral_g
        
        # Apply shape factor
        fy_shaped = fy / self.config.lateral_factor
        
        # Apply stability margin
        max_total = 1.0 - self.config.stability_margin
        
        if fy_shaped >= max_total:
            return 0.0
        
        # fx_max = sqrt(max² - fy²)
        fx_available = math.sqrt(max_total**2 - fy_shaped**2)
        
        # Convert back to g
        return fx_available * max_longitudinal_g * self.config.longitudinal_factor
    
    def compute_combined_limit_speed(
        self,
        corner_radius_m: float,
        braking_g: float,
        max_lateral_g: float = 1.2,
        max_longitudinal_g: float = 1.0
    ) -> float:
        """
        Compute maximum corner speed while trail braking.
        
        Args:
            corner_radius_m: Corner radius
            braking_g: Current braking deceleration
            max_lateral_g: Maximum lateral grip
            max_longitudinal_g: Maximum longitudinal grip
            
        Returns:
            Maximum speed in m/s
        """
        # Compute available lateral
        available_lateral = self.compute_available_lateral(
            braking_g, max_longitudinal_g, max_lateral_g
        )
        
        if available_lateral <= 0:
            return 0.0
        
        if corner_radius_m <= 0 or corner_radius_m == float('inf'):
            return float('inf')
        
        # v = sqrt(a * r)
        g = 9.81
        v = math.sqrt(available_lateral * g * corner_radius_m)
        
        return v
    
    def explain_friction_circle(
        self,
        longitudinal_g: float,
        lateral_g: float
    ) -> str:
        """Generate explanation of current grip usage."""
        
        envelope = self.compute_grip_usage(longitudinal_g, lateral_g)
        
        total = envelope.total_grip_used
        remaining = envelope.grip_remaining
        
        return (
            f"Longitudinal: {abs(longitudinal_g):.2f}g "
            f"({'braking' if longitudinal_g < 0 else 'acceleration'})\n"
            f"Lateral: {abs(lateral_g):.2f}g "
            f"({'left' if lateral_g > 0 else 'right'})\n"
            f"Total grip used: {total*100:.0f}%\n"
            f"Grip remaining: {remaining*100:.0f}%\n"
            f"Stability margin: {self.config.stability_margin*100:.0f}%"
        )
