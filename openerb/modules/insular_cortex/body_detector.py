"""Body detector - Robot body identification and characterization.

This module identifies the physical robot platform and extracts its
hardware characteristics, firmware version, and structural parameters.

Supported robots:
- G1-EDU: Humanoid robot with 26 DOF
- Go2: Quadruped robot with 12 DOF
- Go1: Quadruped robot with 12 DOF
"""

import logging
from typing import Optional, Dict, Any
from openerb.core.types import RobotType, RobotProfile

logger = logging.getLogger(__name__)


class BodyDetector:
    """Detect and characterize physical robot bodies.
    
    This detector identifies the robot model, hardware specifications,
    and firmware characteristics to enable model-aware code generation
    and skill adaptation.
    
    Example:
        >>> detector = BodyDetector()
        >>> body_type = detector.identify_robot("G1-EDU", "1.2.0")
        >>> profile = detector.get_profile(body_type)
    """

    # Robot model identifiers
    ROBOT_MODELS = {
        "G1": {
            "type": RobotType.G1,
            "aliases": ["G1-EDU", "G1-EDU-BASE", "G1-EDU-PRO"],
            "dof": 26,
            "has_gripper": True,
            "is_humanoid": True,
            "weight_kg": 25.0,
        },
        "Go2": {
            "type": RobotType.GO2,
            "aliases": ["Go2", "GO2", "go2"],
            "dof": 12,
            "has_gripper": False,
            "is_humanoid": False,
            "weight_kg": 15.0,
        },
        "Go1": {
            "type": RobotType.GO1,
            "aliases": ["Go1", "GO1", "go1"],
            "dof": 12,
            "has_gripper": False,
            "is_humanoid": False,
            "weight_kg": 12.0,
        },
    }

    # Firmware version compatibility matrix
    FIRMWARE_COMPATIBILITY = {
        RobotType.G1: {
            "min_version": "1.0.0",
            "max_version": "2.0.0",
            "recommended": "1.5.0",
        },
        RobotType.GO2: {
            "min_version": "1.0.0",
            "max_version": "2.0.0",
            "recommended": "1.5.0",
        },
        RobotType.GO1: {
            "min_version": "1.0.0",
            "max_version": "2.0.0",
            "recommended": "1.5.0",
        },
    }

    def __init__(self):
        """Initialize body detector."""
        logger.debug("Initialized BodyDetector")

    def identify_robot(
        self,
        model_name: str,
        firmware_version: Optional[str] = None,
    ) -> RobotType:
        """Identify robot type from model name and firmware version.

        Args:
            model_name: Robot model name (e.g., "G1-EDU", "Go2")
            firmware_version: Optional firmware version for compatibility check

        Returns:
            RobotType enum value

        Raises:
            ValueError: If model is not recognized
        """
        # Normalize model name (case-insensitive)
        model_name_normalized = model_name.upper().replace("-", "")

        # Try exact match first
        for model_key, model_info in self.ROBOT_MODELS.items():
            if model_name == model_key or model_name == model_info["type"].value:
                return model_info["type"]

        # Try alias matching
        for model_key, model_info in self.ROBOT_MODELS.items():
            for alias in model_info["aliases"]:
                if model_name == alias or model_name_normalized == alias.upper().replace("-", ""):
                    return model_info["type"]

        logger.error(f"Unknown robot model: {model_name}")
        raise ValueError(f"Unknown robot model: {model_name}")

    def get_profile(self, robot_type: RobotType) -> Dict[str, Any]:
        """Get detailed hardware profile for a robot type.

        Args:
            robot_type: The robot type

        Returns:
            Dictionary with hardware specifications

        Raises:
            ValueError: If robot type is not supported
        """
        for model_key, model_info in self.ROBOT_MODELS.items():
            if model_info["type"] == robot_type:
                return model_info.copy()

        logger.error(f"Unsupported robot type: {robot_type}")
        raise ValueError(f"Unsupported robot type: {robot_type}")

    def verify_firmware_compatibility(
        self,
        robot_type: RobotType,
        firmware_version: str,
    ) -> tuple[bool, Optional[str]]:
        """Verify firmware version compatibility with robot type.

        Args:
            robot_type: The robot type
            firmware_version: Firmware version string (e.g., "1.2.0")

        Returns:
            Tuple of (is_compatible, warning_message)
            - is_compatible: True if version is within supported range
            - warning_message: Non-empty if version is not recommended
        """
        if robot_type not in self.FIRMWARE_COMPATIBILITY:
            return False, f"No firmware info for {robot_type}"

        compat_info = self.FIRMWARE_COMPATIBILITY[robot_type]
        min_ver = self._parse_version(compat_info["min_version"])
        max_ver = self._parse_version(compat_info["max_version"])
        rec_ver = self._parse_version(compat_info["recommended"])
        fw_ver = self._parse_version(firmware_version)

        if fw_ver < min_ver or fw_ver > max_ver:
            return False, f"Firmware {firmware_version} not in supported range ({compat_info['min_version']}-{compat_info['max_version']})"

        if fw_ver != rec_ver:
            return True, f"Firmware {firmware_version} is not the recommended version ({compat_info['recommended']})"

        return True, None

    def _parse_version(self, version_str: str) -> tuple[int, int, int]:
        """Parse version string to tuple of integers.

        Args:
            version_str: Version string like "1.2.0"

        Returns:
            Tuple of (major, minor, patch)

        Raises:
            ValueError: If version format is invalid
        """
        try:
            parts = version_str.split(".")
            if len(parts) < 3:
                parts.extend(["0"] * (3 - len(parts)))
            return tuple(int(p) for p in parts[:3])  # type: ignore
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid version format: {version_str}") from e

    def get_dof_count(self, robot_type: RobotType) -> int:
        """Get degrees of freedom for robot type.

        Args:
            robot_type: The robot type

        Returns:
            Number of degrees of freedom (DOF)
        """
        profile = self.get_profile(robot_type)
        return profile["dof"]

    def is_humanoid(self, robot_type: RobotType) -> bool:
        """Check if robot is humanoid.

        Args:
            robot_type: The robot type

        Returns:
            True if humanoid, False otherwise
        """
        profile = self.get_profile(robot_type)
        return profile["is_humanoid"]

    def has_gripper(self, robot_type: RobotType) -> bool:
        """Check if robot has gripper capability.

        Args:
            robot_type: The robot type

        Returns:
            True if has gripper, False otherwise
        """
        profile = self.get_profile(robot_type)
        return profile["has_gripper"]
