"""Danger assessment - Risk level determination and classification.

This module assesses the danger level of actions and situations,
classifying risk as GREEN (safe), YELLOW (caution), or RED (critical).
"""

import logging
from typing import Optional, Dict
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class DangerLevel(Enum):
    """Risk level classification."""

    GREEN = "green"  # Safe, no special precautions needed
    YELLOW = "yellow"  # Caution, monitor closely
    RED = "red"  # Critical, should not proceed


@dataclass
class DangerAssessment:
    """Result of danger assessment."""

    level: DangerLevel
    risk_score: float  # 0-100
    primary_risks: list
    mitigation_strategies: list
    requires_confirmation: bool


class DangerAssessor:
    """Assess danger level of actions and situations.
    
    This assessor determines the risk level using multiple factors
    including action type, environmental conditions, and robot state.
    
    Example:
        >>> assessor = DangerAssessor()
        >>> assessment = assessor.assess_action("jump", height=0.5)
        >>> if assessment.level == DangerLevel.RED:
        ...     request_user_confirmation()
    """

    # Risk factors for different actions (0-100 scale)
    ACTION_RISK_FACTORS = {
        # Low-risk actions (0-20)
        "move": 15,
        "see": 5,
        "scan": 5,
        "think": 0,
        "learn": 0,

        # Medium-risk actions (30-60)
        "push": 45,
        "pull": 45,
        "rotate": 40,
        "grasp": 35,
        "pick": 40,

        # High-risk actions (70+)
        "jump": 80,
        "run": 70,
        "kick": 85,
        "punch": 90,
        "drop": 75,
    }

    # Multipliers based on environmental conditions
    ENVIRONMENT_MULTIPLIERS = {
        "low_battery": 1.5,  # Risk increases with low battery
        "obstacles_nearby": 1.4,
        "high_temperature": 1.3,
        "sensors_offline": 1.6,
        "on_stairs": 2.0,  # Extreme risk multiplier
        "near_human": 1.8,
        "unstable_surface": 1.5,
    }

    # Risk thresholds
    RISK_THRESHOLDS = {
        DangerLevel.GREEN: (0, 40),    # 0-40 is green
        DangerLevel.YELLOW: (40, 70),  # 40-70 is yellow
        DangerLevel.RED: (70, 100),    # 70-100 is red
    }

    def __init__(self):
        """Initialize danger assessor."""
        logger.debug("Initialized DangerAssessor")

    def assess_action(
        self,
        action_name: str,
        parameters: Optional[Dict] = None,
        environment: Optional[Dict] = None,
    ) -> DangerAssessment:
        """Assess danger level of an action.

        Args:
            action_name: Name of the action
            parameters: Action parameters
            environment: Environmental conditions

        Returns:
            DangerAssessment with risk level and strategies
        """
        parameters = parameters or {}
        environment = environment or {}

        # Get base risk factor
        base_risk = self.ACTION_RISK_FACTORS.get(action_name, 50)

        # Apply environment multipliers
        risk_multiplier = 1.0
        active_risks = []

        if environment.get("battery_level", 100) < 20:
            risk_multiplier *= self.ENVIRONMENT_MULTIPLIERS["low_battery"]
            active_risks.append("Low battery level")

        if environment.get("obstacles_nearby", False):
            risk_multiplier *= self.ENVIRONMENT_MULTIPLIERS["obstacles_nearby"]
            active_risks.append("Obstacles nearby")

        if environment.get("temperature_celsius", 25) > 70:
            risk_multiplier *= self.ENVIRONMENT_MULTIPLIERS["high_temperature"]
            active_risks.append("Robot overheating")

        if not environment.get("all_sensors_operational", True):
            risk_multiplier *= self.ENVIRONMENT_MULTIPLIERS["sensors_offline"]
            active_risks.append("Sensors offline")

        if environment.get("on_stairs", False):
            risk_multiplier *= self.ENVIRONMENT_MULTIPLIERS["on_stairs"]
            active_risks.append("On stairs (extreme risk)")

        if environment.get("near_human", False):
            risk_multiplier *= self.ENVIRONMENT_MULTIPLIERS["near_human"]
            active_risks.append("Operating near human")

        if not environment.get("stable_surface", True):
            risk_multiplier *= self.ENVIRONMENT_MULTIPLIERS["unstable_surface"]
            active_risks.append("On unstable surface")

        # Apply parameter-based adjustments
        if action_name in ["jump", "run"]:
            speed = parameters.get("speed", 0)
            if speed > 1.5:
                risk_multiplier *= 1.2
                active_risks.append(f"High speed ({speed} m/s)")

        if action_name in ["grasp", "push", "pull"]:
            force = parameters.get("force", 0)
            if force > 80:
                risk_multiplier *= 1.3
                active_risks.append(f"High force ({force}N)")

        # Calculate final risk score
        risk_score = min(100, base_risk * risk_multiplier)

        # Determine danger level
        danger_level = self._get_danger_level(risk_score)

        # Generate mitigation strategies
        strategies = self._get_mitigation_strategies(
            action_name, danger_level, active_risks
        )

        # Determine if confirmation is needed
        requires_confirmation = danger_level in [
            DangerLevel.YELLOW,
            DangerLevel.RED,
        ]

        return DangerAssessment(
            level=danger_level,
            risk_score=round(risk_score, 1),
            primary_risks=active_risks,
            mitigation_strategies=strategies,
            requires_confirmation=requires_confirmation,
        )

    def _get_danger_level(self, risk_score: float) -> DangerLevel:
        """Determine danger level from risk score.

        Args:
            risk_score: Risk score (0-100)

        Returns:
            DangerLevel enum
        """
        if risk_score < 40:
            return DangerLevel.GREEN
        elif risk_score < 70:
            return DangerLevel.YELLOW
        else:
            return DangerLevel.RED

    def _get_mitigation_strategies(
        self,
        action_name: str,
        danger_level: DangerLevel,
        risks: list,
    ) -> list:
        """Get mitigation strategies for identified risks.

        Args:
            action_name: Name of the action
            danger_level: Current danger level
            risks: List of identified risks

        Returns:
            List of mitigation strategy strings
        """
        strategies = []

        # Action-specific strategies
        if action_name in ["jump", "run"] and danger_level != DangerLevel.GREEN:
            strategies.append("Reduce speed and acceleration")
            strategies.append("Ensure clear landing/movement area")

        if action_name in ["grasp", "push", "pull"] and danger_level != DangerLevel.GREEN:
            strategies.append("Start with reduced force")
            strategies.append("Monitor force feedback continuously")

        # Risk-specific strategies
        if "Low battery" in risks:
            strategies.append("Reduce task complexity")
            strategies.append("Plan route to charging station")

        if "Obstacles nearby" in risks:
            strategies.append("Use obstacle avoidance")
            strategies.append("Move slowly and cautiously")

        if "Robot overheating" in risks:
            strategies.append("Reduce intensity of operations")
            strategies.append("Allow cooling period")

        if "Sensors offline" in risks:
            strategies.append("Return to base for diagnostics")
            strategies.append("Avoid navigation-heavy tasks")

        if "On stairs" in risks:
            strategies.append("Use extreme caution")
            strategies.append("Move very slowly")
            strategies.append("Request human supervision")

        if "Operating near human" in risks:
            strategies.append("Reduce speed to safe level")
            strategies.append("Maintain safety distance")
            strategies.append("Alert nearby humans")

        if "On unstable surface" in risks:
            strategies.append("Reduce movement speed")
            strategies.append("Avoid heavy manipulations")

        # Default strategies for high danger
        if danger_level == DangerLevel.RED:
            if not strategies:
                strategies.append("Abort action and return to safe state")
            strategies.append("Request human intervention")

        return strategies

    def get_risk_comparison(
        self,
        actions: list,
        environment: Optional[Dict] = None,
    ) -> list:
        """Compare risk levels of multiple actions.

        Args:
            actions: List of action names to compare
            environment: Environmental conditions

        Returns:
            List of actions sorted by risk (ascending)
        """
        assessments = []

        for action in actions:
            assessment = self.assess_action(action, {}, environment or {})
            assessments.append({
                "action": action,
                "level": assessment.level.value,
                "risk_score": assessment.risk_score,
            })

        # Sort by risk score
        return sorted(assessments, key=lambda x: x["risk_score"])

    def get_safest_action(
        self,
        actions: list,
        environment: Optional[Dict] = None,
    ) -> str:
        """Find the safest action from a list.

        Args:
            actions: List of action names
            environment: Environmental conditions

        Returns:
            Name of safest action
        """
        comparison = self.get_risk_comparison(actions, environment)
        return comparison[0]["action"] if comparison else None
