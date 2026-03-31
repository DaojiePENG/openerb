"""Insular Cortex (岛叶皮层) - Robot body self-awareness module.

The Insular Cortex provides self-awareness about the robot's physical body,
including identification, capability assessment, and body-aware skill management.

This module handles:
- Robot body identification (hardware model detection)
- Capability mapping (what the robot can do)
- Skill classification (universal vs body-specific)
- Compatibility validation
- Robot-aware code generation support
"""

import logging
from typing import Optional, List, Dict
from openerb.core.types import Skill, SkillType, RobotType
from openerb.modules.insular_cortex.body_detector import BodyDetector
from openerb.modules.insular_cortex.capability_mapper import CapabilityMapper
from openerb.modules.insular_cortex.skill_classifier import SkillClassifier

logger = logging.getLogger(__name__)


class InsularCortex:
    """Robot body self-awareness and capability management.
    
    The Insular Cortex serves as the robot's proprioceptive system,
    maintaining awareness of its own physical capabilities and limitations.
    This enables:
    
    1. Body Identification: What type of robot am I?
    2. Capability Assessment: What can I do?
    3. Skill Adaptation: Can I run this skill?
    4. Body-Aware Code Generation: Generate code for my specific body
    
    Example:
        >>> from openerb.core.types import RobotType
        >>> cortex = InsularCortex(robot_type=RobotType.G1)
        >>> print(cortex.get_robot_type())
        RobotType.G1
        >>> caps = cortex.get_capabilities()
        >>> if cortex.can_run_skill(some_skill):
        ...     execute(some_skill)
    """

    def __init__(
        self,
        robot_type: Optional[RobotType] = None,
        firmware_version: Optional[str] = None,
    ):
        """Initialize Insular Cortex.

        Args:
            robot_type: Optional robot type (can be set later via identify_robot)
            firmware_version: Optional firmware version for compatibility checking

        Raises:
            ValueError: If robot_type is invalid
        """
        self.robot_type = robot_type
        self.firmware_version = firmware_version
        self.body_detector = BodyDetector()
        self.capability_mapper = CapabilityMapper()
        self.skill_classifier = SkillClassifier(self.capability_mapper)

        logger.info(f"Initialized InsularCortex for {robot_type}")

    def identify_robot(
        self,
        model_name: str,
        firmware_version: Optional[str] = None,
    ) -> RobotType:
        """Identify the robot body from model name and firmware.

        Args:
            model_name: Robot model name (e.g., "G1-EDU", "Go2")
            firmware_version: Optional firmware version

        Returns:
            Identified RobotType

        Raises:
            ValueError: If model is not recognized
        """
        self.robot_type = self.body_detector.identify_robot(model_name)
        self.firmware_version = firmware_version

        if firmware_version:
            is_compat, warning = self.body_detector.verify_firmware_compatibility(
                self.robot_type, firmware_version
            )
            if not is_compat:
                logger.warning(f"Firmware compatibility issue: {warning}")
            elif warning:
                logger.info(f"Firmware note: {warning}")

        logger.info(f"Identified robot: {self.robot_type}")
        return self.robot_type

    def get_robot_type(self) -> Optional[RobotType]:
        """Get the current robot type.

        Returns:
            Current RobotType, or None if not identified
        """
        return self.robot_type

    def get_robot_profile(self) -> Dict:
        """Get detailed hardware profile of current robot.

        Returns:
            Dictionary with hardware specifications

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified. Call identify_robot() first.")
        return self.body_detector.get_profile(self.robot_type)

    def get_dof_count(self) -> int:
        """Get degrees of freedom of current robot.

        Returns:
            Number of DOF

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.body_detector.get_dof_count(self.robot_type)

    def is_humanoid(self) -> bool:
        """Check if current robot is humanoid.

        Returns:
            True if humanoid, False if quadruped

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.body_detector.is_humanoid(self.robot_type)

    def has_gripper(self) -> bool:
        """Check if current robot has gripper.

        Returns:
            True if has gripper, False otherwise

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.body_detector.has_gripper(self.robot_type)

    def get_capabilities(
        self,
        category: Optional[str] = None,
    ) -> Dict:
        """Get capabilities of current robot.

        Args:
            category: Optional capability category filter

        Returns:
            Dictionary of capabilities

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.capability_mapper.get_capabilities(self.robot_type, category)

    def has_capability(self, capability_name: str) -> bool:
        """Check if robot has a specific capability.

        Args:
            capability_name: Capability to check (e.g., "grasp", "lidar")

        Returns:
            True if robot has capability

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.capability_mapper.has_capability(self.robot_type, capability_name)

    def get_enabled_capabilities(self, category: Optional[str] = None) -> List[str]:
        """Get all enabled capabilities.

        Args:
            category: Optional category filter

        Returns:
            List of enabled capability names

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.capability_mapper.get_enabled_capabilities(self.robot_type, category)

    def get_disabled_capabilities(self, category: Optional[str] = None) -> List[str]:
        """Get all disabled capabilities.

        Args:
            category: Optional category filter

        Returns:
            List of disabled capability names

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.capability_mapper.get_disabled_capabilities(self.robot_type, category)

    def classify_skill(self, skill: Skill) -> SkillType:
        """Classify a skill (universal or body-specific).

        Args:
            skill: The skill to classify

        Returns:
            SkillType enum

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.skill_classifier.classify_skill(skill, self.robot_type)

    def can_run_skill(self, skill: Skill) -> bool:
        """Check if current robot can run a skill.

        Args:
            skill: The skill to check

        Returns:
            True if skill is compatible

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.skill_classifier.is_skill_compatible(skill, self.robot_type)

    def get_incompatible_capabilities(self, skill: Skill) -> List[str]:
        """Get missing capabilities for a skill.

        Args:
            skill: The skill to check

        Returns:
            List of missing capability names

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.skill_classifier.get_incompatible_capabilities(skill, self.robot_type)

    def get_adaptation_suggestion(self, skill: Skill) -> Optional[str]:
        """Get suggestions for adapting a skill to current robot.

        Args:
            skill: The skill to adapt

        Returns:
            Adaptation suggestion string, or None if already compatible

        Raises:
            ValueError: If robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.skill_classifier.adapt_skill_for_robot(skill, self.robot_type)

    def compare_with_robot(self, other_robot_type: RobotType) -> Dict:
        """Compare capabilities with another robot type.

        Args:
            other_robot_type: Robot type to compare with

        Returns:
            Dictionary with shared, unique capabilities

        Raises:
            ValueError: If current robot type not set
        """
        if not self.robot_type:
            raise ValueError("Robot type not identified")
        return self.capability_mapper.compare_capabilities(
            self.robot_type, other_robot_type
        )

    def __repr__(self) -> str:
        return f"InsularCortex(robot_type={self.robot_type}, firmware={self.firmware_version})"
