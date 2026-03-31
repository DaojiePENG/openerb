"""Skill classifier - Classify skills by robot compatibility.

This module classifies skills as universal (works on all robots) or
body-specific (requires certain hardware), enabling smart skill selection
and compatibility validation.
"""

import logging
from typing import List, Optional
from openerb.core.types import Skill, SkillType, RobotType

logger = logging.getLogger(__name__)


class SkillClassifier:
    """Classify skills by robot compatibility requirements.
    
    This classifier determines whether a skill can run on a given robot
    by checking hardware requirements, detecting incompatibilities, and
    suggesting adaptations.
    
    Example:
        >>> classifier = SkillClassifier()
        >>> skill_type = classifier.classify_skill(skill, RobotType.G1)
        >>> compatible = classifier.is_skill_compatible(skill, RobotType.GO2)
    """

    # Skill requirements by capability
    CAPABILITY_REQUIREMENTS = {
        # Movement skills
        "walk": ["movement.walk"],
        "run": ["movement.run"],
        "jump": ["movement.jump"],
        "crouch": ["movement.crouch"],
        "trot": ["movement.trot"],
        "backward": ["movement.backward"],

        # Manipulation skills
        "grasp": ["manipulation.grasp", "perception.force_sensing"],
        "pick": ["manipulation.grasp", "perception.force_sensing", "perception.camera"],
        "place": ["manipulation.grasp", "perception.force_sensing"],
        "push": ["manipulation.push"],
        "pull": ["manipulation.pull"],
        "manipulate": ["manipulation.fine_manipulation"],
        "rotate": ["manipulation.rotate_object"],

        # Perception skills
        "see": ["perception.camera"],
        "scan": ["perception.lidar"],
        "sense": ["perception.imu"],
        "touch": ["perception.force_sensing"],

        # Learning skills
        "learn": [],  # Universal
        "memorize": [],  # Universal
        "execute": [],  # Universal
    }

    def __init__(self, capability_mapper=None):
        """Initialize skill classifier.

        Args:
            capability_mapper: Optional CapabilityMapper instance for capability checks
        """
        from openerb.modules.insular_cortex.capability_mapper import CapabilityMapper

        self.capability_mapper = capability_mapper or CapabilityMapper()
        logger.debug("Initialized SkillClassifier")

    def classify_skill(
        self,
        skill: Skill,
        robot_type: RobotType,
    ) -> SkillType:
        """Classify a skill based on robot compatibility.

        Args:
            skill: The skill to classify
            robot_type: The robot type to classify for

        Returns:
            SkillType enum (UNIVERSAL or BODY_SPECIFIC)
        """
        # Universal skills that work on all robots
        universal_keywords = [
            "learn", "memorize", "execute", "plan", "parse", "recognize", "think"
        ]

        if any(keyword in skill.name.lower() for keyword in universal_keywords):
            return SkillType.UNIVERSAL

        # Check if skill has hardware-specific requirements
        if self.is_skill_universal(skill):
            return SkillType.UNIVERSAL

        return SkillType.BODY_SPECIFIC

    def is_skill_universal(self, skill: Skill) -> bool:
        """Determine if a skill is universal (works on all robots).

        Args:
            skill: The skill to check

        Returns:
            True if skill works on all robots, False if body-specific
        """
        # Extract required capabilities from skill description and tags
        skill_requirements = []

        # Parse from skill name and description
        skill_text = f"{skill.name} {skill.description}".lower()
        for action, requirements in self.CAPABILITY_REQUIREMENTS.items():
            if action in skill_text and requirements:
                skill_requirements.extend(requirements)

        # If no specific hardware requirements found, it's universal
        if not skill_requirements:
            return True

        return False

    def is_skill_compatible(
        self,
        skill: Skill,
        robot_type: RobotType,
    ) -> bool:
        """Check if a skill is compatible with a robot type.

        Args:
            skill: The skill to check
            robot_type: The robot type

        Returns:
            True if skill is compatible, False otherwise
        """
        # Check if skill explicitly lists supported robots
        if skill.supported_robots:
            # If supported_robots list exists and is not empty,
            # robot must be in the list
            if robot_type not in skill.supported_robots:
                return False
            # If robot is in supported list, check capabilities
            required_caps = self._extract_required_capabilities(skill)
            if not required_caps:
                return True
            # Check if robot has all required capabilities
            for cap in required_caps:
                # Handle both "walk" and "movement.walk" formats
                cap_name = cap.split('.')[-1] if '.' in cap else cap
                if not self.capability_mapper.has_capability(robot_type, cap_name):
                    return False
            return True

        # If no supported_robots list specified, check requirements
        required_caps = self._extract_required_capabilities(skill)

        # If no explicit requirements detected, assume it's compatible
        if not required_caps:
            return True

        # Check if robot has all required capabilities
        for cap in required_caps:
            # Handle both "walk" and "movement.walk" formats
            cap_name = cap.split('.')[-1] if '.' in cap else cap
            if not self.capability_mapper.has_capability(robot_type, cap_name):
                return False

        return True

    def get_incompatible_capabilities(
        self,
        skill: Skill,
        robot_type: RobotType,
    ) -> List[str]:
        """Get list of missing capabilities for a skill on a robot.

        Args:
            skill: The skill to check
            robot_type: The robot type

        Returns:
            List of missing capability names, empty if all present
        """
        required_caps = self._extract_required_capabilities(skill)
        missing = []

        for cap in required_caps:
            # Handle both "walk" and "movement.walk" formats
            cap_name = cap.split('.')[-1] if '.' in cap else cap
            if not self.capability_mapper.has_capability(robot_type, cap_name):
                missing.append(cap_name)

        return missing

    def suggest_compatible_robots(
        self,
        skill: Skill,
        available_robots: List[RobotType],
    ) -> List[RobotType]:
        """Suggest which robots can run a given skill.

        Args:
            skill: The skill to check
            available_robots: List of available robot types

        Returns:
            List of compatible robot types
        """
        return [
            robot for robot in available_robots
            if self.is_skill_compatible(skill, robot)
        ]

    def _extract_required_capabilities(self, skill: Skill) -> List[str]:
        """Extract required capabilities from a skill.

        Args:
            skill: The skill to analyze

        Returns:
            List of required capability names
        """
        required = []
        skill_name = skill.name.lower()
        skill_desc = skill.description.lower() if skill.description else ""
        tags_text = " ".join(skill.tags).lower() if skill.tags else ""
        combined_text = f"{skill_name} {skill_desc} {tags_text}"

        # Check skill name and description for action keywords
        for action, requirements in self.CAPABILITY_REQUIREMENTS.items():
            if action in combined_text:
                if requirements:  # If has specific requirements
                    required.extend(requirements)

        return list(set(required))  # Remove duplicates

    def adapt_skill_for_robot(
        self,
        skill: Skill,
        robot_type: RobotType,
    ) -> Optional[str]:
        """Suggest adaptations for running a skill on a robot.

        Args:
            skill: The skill to adapt
            robot_type: The target robot type

        Returns:
            Adaptation suggestion string, or None if already compatible
        """
        if self.is_skill_compatible(skill, robot_type):
            return None

        missing = self.get_incompatible_capabilities(skill, robot_type)
        profile = self.capability_mapper.get_capabilities(robot_type)

        suggestions = []

        # Map missing capabilities to alternative actions
        capability_alternatives = {
            "manipulation.grasp": "Try push-based interactions instead of grasping",
            "perception.lidar": "Use camera-based obstacle avoidance instead",
            "perception.force_sensing": "Use velocity control instead of force control",
            "movement.jump": "Use high-speed running instead of jumping",
        }

        for missing_cap in missing:
            if missing_cap in capability_alternatives:
                suggestions.append(capability_alternatives[missing_cap])
            else:
                suggestions.append(f"Missing capability: {missing_cap}")

        return "; ".join(suggestions) if suggestions else None
