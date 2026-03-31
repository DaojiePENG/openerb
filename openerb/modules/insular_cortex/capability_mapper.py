"""Capability mapper - Robot capability discovery and mapping.

This module maps robot hardware specifications to software capabilities,
enabling skill selection and robot-aware code generation.
"""

import logging
from typing import List, Dict, Set, Optional
from openerb.core.types import RobotType

logger = logging.getLogger(__name__)


class CapabilityMapper:
    """Map hardware specifications to software capabilities.
    
    This mapper provides a database of what each robot model can do,
    supporting queries like "does this robot have a gripper?" or
    "what manipulation skills are available?"
    
    Example:
        >>> mapper = CapabilityMapper()
        >>> caps = mapper.get_capabilities(RobotType.G1)
        >>> if mapper.has_capability(RobotType.G1, "manipulation"):
        ...     print("Can manipulate objects")
    """

    # Hardware-to-capability mapping
    CAPABILITY_DATABASE = {
        RobotType.G1: {
            "movement": {
                "walk": True,
                "run": True,
                "jump": True,
                "crouch": True,
                "balance": True,
                "turn": True,
                "side_step": True,
            },
            "manipulation": {
                "grasp": True,
                "pinch": True,
                "push": True,
                "pull": True,
                "rotate_object": True,
                "fine_manipulation": True,
            },
            "perception": {
                "camera": True,
                "lidar": True,
                "imu": True,
                "joint_sensors": True,
                "force_sensing": True,
            },
            "communication": {
                "wifi": True,
                "bluetooth": False,
                "network": True,
            },
            "computation": {
                "on_board_compute": True,
                "gpu": False,
                "max_compute_power_watts": 50,
            },
        },
        RobotType.GO2: {
            "movement": {
                "walk": True,
                "run": True,
                "jump": True,
                "trot": True,
                "balance": True,
                "turn": True,
                "backward": True,
            },
            "manipulation": {
                "grasp": False,
                "pinch": False,
                "push": True,
                "rotate_object": False,
            },
            "perception": {
                "camera": True,
                "lidar": True,
                "imu": True,
                "joint_sensors": True,
                "force_sensing": False,
            },
            "communication": {
                "wifi": True,
                "bluetooth": True,
                "network": True,
            },
            "computation": {
                "on_board_compute": True,
                "gpu": False,
                "max_compute_power_watts": 40,
            },
        },
        RobotType.GO1: {
            "movement": {
                "walk": True,
                "run": True,
                "jump": False,
                "trot": True,
                "balance": True,
                "turn": True,
                "backward": True,
            },
            "manipulation": {
                "grasp": False,
                "pinch": False,
                "push": True,
                "rotate_object": False,
            },
            "perception": {
                "camera": True,
                "lidar": False,
                "imu": True,
                "joint_sensors": True,
                "force_sensing": False,
            },
            "communication": {
                "wifi": True,
                "bluetooth": True,
                "network": True,
            },
            "computation": {
                "on_board_compute": True,
                "gpu": False,
                "max_compute_power_watts": 30,
            },
        },
    }

    def __init__(self):
        """Initialize capability mapper."""
        logger.debug("Initialized CapabilityMapper")

    def get_capabilities(
        self,
        robot_type: RobotType,
        category: Optional[str] = None,
    ) -> Dict[str, Dict[str, bool]]:
        """Get capabilities for a robot type.

        Args:
            robot_type: The robot type
            category: Optional category filter (e.g., "movement", "manipulation")

        Returns:
            Dictionary of capabilities, optionally filtered by category

        Raises:
            ValueError: If robot type is not supported
        """
        if robot_type not in self.CAPABILITY_DATABASE:
            raise ValueError(f"Unknown robot type: {robot_type}")

        caps = self.CAPABILITY_DATABASE[robot_type]

        if category:
            if category not in caps:
                raise ValueError(f"Unknown capability category: {category}")
            return {category: caps[category]}

        return caps

    def has_capability(
        self,
        robot_type: RobotType,
        capability_name: str,
    ) -> bool:
        """Check if robot has a specific capability.

        Args:
            robot_type: The robot type
            capability_name: Capability to check (e.g., "grasp", "lidar")

        Returns:
            True if robot has the capability, False otherwise
        """
        caps = self.get_capabilities(robot_type)

        for category_caps in caps.values():
            if capability_name in category_caps:
                return category_caps[capability_name]

        return False

    def get_enabled_capabilities(
        self,
        robot_type: RobotType,
        category: Optional[str] = None,
    ) -> List[str]:
        """Get all enabled capabilities for a robot type.

        Args:
            robot_type: The robot type
            category: Optional category filter

        Returns:
            List of enabled capability names
        """
        caps = self.get_capabilities(robot_type, category)
        enabled = []

        for cat_name, cat_caps in caps.items():
            if isinstance(cat_caps, dict):
                for cap_name, is_enabled in cat_caps.items():
                    if isinstance(is_enabled, bool) and is_enabled:
                        enabled.append(cap_name)

        return enabled

    def get_disabled_capabilities(
        self,
        robot_type: RobotType,
        category: Optional[str] = None,
    ) -> List[str]:
        """Get all disabled capabilities for a robot type.

        Args:
            robot_type: The robot type
            category: Optional category filter

        Returns:
            List of disabled capability names
        """
        caps = self.get_capabilities(robot_type, category)
        disabled = []

        for cat_name, cat_caps in caps.items():
            if isinstance(cat_caps, dict):
                for cap_name, is_enabled in cat_caps.items():
                    if isinstance(is_enabled, bool) and not is_enabled:
                        disabled.append(cap_name)

        return disabled

    def compare_capabilities(
        self,
        robot_type1: RobotType,
        robot_type2: RobotType,
    ) -> Dict[str, any]:
        """Compare capabilities between two robot types.

        Args:
            robot_type1: First robot type
            robot_type2: Second robot type

        Returns:
            Dictionary with shared, unique1, and unique2 capabilities
        """
        caps1 = set(self.get_enabled_capabilities(robot_type1))
        caps2 = set(self.get_enabled_capabilities(robot_type2))

        return {
            "shared": sorted(list(caps1 & caps2)),
            "only_in_first": sorted(list(caps1 - caps2)),
            "only_in_second": sorted(list(caps2 - caps1)),
        }

    def filter_by_capabilities(
        self,
        robots: List[RobotType],
        required_capabilities: List[str],
    ) -> List[RobotType]:
        """Filter robots by required capabilities.

        Args:
            robots: List of robot types to filter
            required_capabilities: List of required capability names

        Returns:
            List of robots that have all required capabilities
        """
        result = []
        for robot in robots:
            if all(self.has_capability(robot, cap) for cap in required_capabilities):
                result.append(robot)
        return result
