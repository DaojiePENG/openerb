"""Safety evaluator - Evaluate action safety before execution.

This module assesses whether a planned action is safe to execute,
considering:
- Action type and parameters
- Robot's current state
- Environmental context
- Safety constraints and limits
"""

import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Safety level classification."""

    SAFE = "safe"  # Can execute without restrictions
    CAUTION = "caution"  # Can execute with precautions
    DANGEROUS = "dangerous"  # Should not execute
    CRITICAL = "critical"  # Must not execute


@dataclass
class SafetyCheck:
    """Result of a safety check."""

    level: SafetyLevel
    passed: bool
    reason: str
    recommendations: List[str]


class SafetyEvaluator:
    """Evaluate action safety before execution.
    
    This evaluator checks various safety criteria to determine
    whether an action can be safely executed by the robot.
    
    Example:
        >>> evaluator = SafetyEvaluator()
        >>> check = evaluator.evaluate_action("grasp", {"force": 50})
        >>> if check.passed:
        ...     execute_action()
    """

    # Safety thresholds for different actions
    ACTION_CONSTRAINTS = {
        "move": {
            "max_speed": 2.0,  # m/s
            "max_acceleration": 1.0,  # m/s^2
            "min_distance_to_obstacle": 0.3,  # meters
        },
        "grasp": {
            "max_force": 100.0,  # Newtons
            "min_object_size": 0.02,  # meters
            "max_object_mass": 2.0,  # kg
        },
        "jump": {
            "max_height": 0.5,  # meters
            "min_ground_clearance": 0.2,  # meters
            "max_forward_distance": 1.0,  # meters
        },
        "rotate": {
            "max_speed": 90.0,  # degrees per second
            "max_acceleration": 45.0,  # degrees per second^2
        },
        "push": {
            "max_force": 150.0,  # Newtons
            "max_duration": 5.0,  # seconds
        },
    }

    # High-risk actions that need extra validation
    HIGH_RISK_ACTIONS = {
        "jump", "push", "pull", "kick", "punch", "drop",
        "rotate_fast", "accelerate_fast"
    }

    # Actions that require force/load monitoring
    FORCE_MONITORED_ACTIONS = {
        "grasp", "push", "pull", "manipulate", "squeeze"
    }

    def __init__(self, strict_mode: bool = False):
        """Initialize safety evaluator.

        Args:
            strict_mode: If True, use stricter safety thresholds
        """
        self.strict_mode = strict_mode
        self.evaluation_history: List[Dict] = []
        logger.debug(f"Initialized SafetyEvaluator (strict_mode={strict_mode})")

    def evaluate_action(
        self,
        action_name: str,
        parameters: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ) -> SafetyCheck:
        """Evaluate safety of an action.

        Args:
            action_name: Name of the action (e.g., "grasp", "move")
            parameters: Action parameters (e.g., {"force": 50})
            context: Environmental context (obstacles, battery, etc.)

        Returns:
            SafetyCheck with level and recommendations
        """
        parameters = parameters or {}
        context = context or {}

        recommendations = []
        level = SafetyLevel.SAFE
        reason = "Action is safe to execute"

        # Check if action is recognized
        if action_name not in self.ACTION_CONSTRAINTS and action_name not in self.HIGH_RISK_ACTIONS:
            logger.warning(f"Unknown action: {action_name}")
            return SafetyCheck(
                level=SafetyLevel.CAUTION,
                passed=True,
                reason="Action not in safety database, but assumed safe",
                recommendations=["Monitor action execution carefully"],
            )

        # Check high-risk actions
        if action_name in self.HIGH_RISK_ACTIONS:
            level = SafetyLevel.CAUTION
            recommendations.append(f"{action_name} is a high-risk action")

        # Check action-specific constraints
        if action_name in self.ACTION_CONSTRAINTS:
            constraint_check = self._check_constraints(
                action_name, parameters
            )
            if not constraint_check["passed"]:
                level = SafetyLevel.DANGEROUS
                reason = constraint_check["reason"]
                recommendations.extend(constraint_check["recommendations"])

        # Check force monitoring requirements
        if action_name in self.FORCE_MONITORED_ACTIONS:
            if "force" in parameters:
                force = parameters["force"]
                if force > self.ACTION_CONSTRAINTS.get(action_name, {}).get("max_force", float("inf")):
                    level = SafetyLevel.DANGEROUS
                    reason = f"Force {force}N exceeds limit"
                    recommendations.append(f"Reduce force to below limit")

        # Check environmental safety
        env_check = self._check_environment(action_name, context)
        if not env_check["passed"]:
            if level == SafetyLevel.SAFE:
                level = SafetyLevel.CAUTION
            reason = env_check["reason"]
            recommendations.extend(env_check["recommendations"])

        # Record evaluation
        self.evaluation_history.append({
            "action": action_name,
            "level": level.value,
            "passed": level != SafetyLevel.DANGEROUS,
            "parameters": parameters,
        })

        return SafetyCheck(
            level=level,
            passed=level != SafetyLevel.DANGEROUS,
            reason=reason,
            recommendations=recommendations,
        )

    def _check_constraints(
        self,
        action_name: str,
        parameters: Dict,
    ) -> Dict:
        """Check action-specific constraints.

        Args:
            action_name: Name of the action
            parameters: Action parameters

        Returns:
            Dictionary with passed flag and details
        """
        constraints = self.ACTION_CONSTRAINTS.get(action_name, {})
        recommendations = []

        for constraint_name, max_value in constraints.items():
            # Extract corresponding parameter
            param_key = constraint_name.replace("max_", "").replace("min_", "")
            if param_key in parameters:
                param_value = parameters[param_key]

                # Check max constraints
                if constraint_name.startswith("max_"):
                    if param_value > max_value:
                        if self.strict_mode:
                            return {
                                "passed": False,
                                "reason": f"{param_key} {param_value} exceeds limit {max_value}",
                                "recommendations": [f"Reduce {param_key} to {max_value}"],
                            }
                        else:
                            recommendations.append(f"Warning: {param_key} near limit")

                # Check min constraints
                elif constraint_name.startswith("min_"):
                    if param_value < max_value:  # max_value is actually min here
                        recommendations.append(f"Warning: {param_key} below recommended {max_value}")

        return {
            "passed": True,
            "reason": "All constraints satisfied",
            "recommendations": recommendations,
        }

    def _check_environment(
        self,
        action_name: str,
        context: Dict,
    ) -> Dict:
        """Check environmental safety.

        Args:
            action_name: Name of the action
            context: Environmental context

        Returns:
            Dictionary with passed flag and details
        """
        recommendations = []

        # Check battery level for intensive operations
        battery_level = context.get("battery_level", 100)
        if action_name in {"jump", "run", "push"} and battery_level < 20:
            recommendations.append("Low battery: avoid intensive operations")

        # Check for obstacles
        distance_to_obstacle = context.get("distance_to_obstacle", float("inf"))
        min_safe_distance = self.ACTION_CONSTRAINTS.get(action_name, {}).get(
            "min_distance_to_obstacle", 0.1
        )
        if distance_to_obstacle < min_safe_distance:
            recommendations.append(f"Obstacle too close: {distance_to_obstacle}m")

        # Check system health
        if not context.get("all_sensors_operational", True):
            recommendations.append("Some sensors not operational")

        # Check temperature
        temperature = context.get("temperature_celsius", 25)
        if temperature > 70:
            recommendations.append("Robot overheating: limit intensive operations")

        return {
            "passed": len(recommendations) == 0 or battery_level >= 20,
            "reason": "Environmental check complete",
            "recommendations": recommendations,
        }

    def can_execute(
        self,
        action_name: str,
        parameters: Optional[Dict] = None,
        context: Optional[Dict] = None,
    ) -> bool:
        """Quick check if action can execute.

        Args:
            action_name: Name of the action
            parameters: Action parameters
            context: Environmental context

        Returns:
            True if safe to execute, False otherwise
        """
        check = self.evaluate_action(action_name, parameters, context)
        return check.passed

    def get_evaluation_history(self, last_n: Optional[int] = None) -> List[Dict]:
        """Get evaluation history.

        Args:
            last_n: Return last N evaluations (None for all)

        Returns:
            List of past evaluations
        """
        if last_n is None:
            return self.evaluation_history.copy()
        return self.evaluation_history[-last_n:]

    def clear_history(self) -> None:
        """Clear evaluation history."""
        self.evaluation_history.clear()

    def get_safety_stats(self) -> Dict:
        """Get safety evaluation statistics.

        Returns:
            Dictionary with stats
        """
        if not self.evaluation_history:
            return {
                "total_evaluations": 0,
                "safe_actions": 0,
                "dangerous_actions": 0,
                "safety_rate": 0.0,
            }

        total = len(self.evaluation_history)
        safe = sum(1 for e in self.evaluation_history if e.get("level") == SafetyLevel.SAFE.value)
        dangerous = sum(1 for e in self.evaluation_history if e.get("level") == SafetyLevel.DANGEROUS.value)

        return {
            "total_evaluations": total,
            "safe_actions": safe,
            "dangerous_actions": dangerous,
            "safety_rate": safe / total if total > 0 else 0.0,
        }
