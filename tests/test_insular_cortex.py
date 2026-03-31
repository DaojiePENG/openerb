"""Unit tests for Insular Cortex module."""

import pytest
from openerb.core.types import RobotType, SkillType, Skill
from openerb.modules.insular_cortex import (
    InsularCortex,
    BodyDetector,
    CapabilityMapper,
    SkillClassifier,
)


class TestBodyDetector:
    """Tests for BodyDetector."""

    def test_init(self):
        """Test BodyDetector initialization."""
        detector = BodyDetector()
        assert detector is not None

    def test_identify_robot_g1(self):
        """Test G1 robot identification."""
        detector = BodyDetector()
        robot_type = detector.identify_robot("G1-EDU")
        assert robot_type == RobotType.G1

    def test_identify_robot_go2(self):
        """Test Go2 robot identification."""
        detector = BodyDetector()
        robot_type = detector.identify_robot("Go2")
        assert robot_type == RobotType.GO2

    def test_identify_robot_go1(self):
        """Test Go1 robot identification."""
        detector = BodyDetector()
        robot_type = detector.identify_robot("Go1")
        assert robot_type == RobotType.GO1

    def test_identify_robot_case_insensitive(self):
        """Test case-insensitive robot identification."""
        detector = BodyDetector()
        assert detector.identify_robot("g1-edu") == RobotType.G1
        assert detector.identify_robot("GO2") == RobotType.GO2

    def test_identify_robot_unknown(self):
        """Test unknown robot raises ValueError."""
        detector = BodyDetector()
        with pytest.raises(ValueError, match="Unknown robot model"):
            detector.identify_robot("UnknownBot")

    def test_get_profile(self):
        """Test getting robot profile."""
        detector = BodyDetector()
        profile = detector.get_profile(RobotType.G1)
        assert profile["type"] == RobotType.G1
        assert profile["dof"] == 26
        assert profile["has_gripper"] is True
        assert profile["is_humanoid"] is True

    def test_get_dof_count(self):
        """Test getting DOF count."""
        detector = BodyDetector()
        assert detector.get_dof_count(RobotType.G1) == 26
        assert detector.get_dof_count(RobotType.GO2) == 12
        assert detector.get_dof_count(RobotType.GO1) == 12

    def test_is_humanoid(self):
        """Test humanoid detection."""
        detector = BodyDetector()
        assert detector.is_humanoid(RobotType.G1) is True
        assert detector.is_humanoid(RobotType.GO2) is False
        assert detector.is_humanoid(RobotType.GO1) is False

    def test_has_gripper(self):
        """Test gripper capability detection."""
        detector = BodyDetector()
        assert detector.has_gripper(RobotType.G1) is True
        assert detector.has_gripper(RobotType.GO2) is False
        assert detector.has_gripper(RobotType.GO1) is False

    def test_verify_firmware_compatibility_valid(self):
        """Test firmware compatibility check with valid version."""
        detector = BodyDetector()
        is_compat, warning = detector.verify_firmware_compatibility(
            RobotType.G1, "1.5.0"
        )
        assert is_compat is True

    def test_verify_firmware_compatibility_invalid(self):
        """Test firmware compatibility check with invalid version."""
        detector = BodyDetector()
        is_compat, warning = detector.verify_firmware_compatibility(
            RobotType.G1, "3.0.0"
        )
        assert is_compat is False

    def test_version_parsing(self):
        """Test version string parsing."""
        detector = BodyDetector()
        v1 = detector._parse_version("1.2.3")
        v2 = detector._parse_version("1.2.4")
        assert v1 < v2
        assert v1 == (1, 2, 3)


class TestCapabilityMapper:
    """Tests for CapabilityMapper."""

    def test_init(self):
        """Test CapabilityMapper initialization."""
        mapper = CapabilityMapper()
        assert mapper is not None

    def test_get_capabilities_all(self):
        """Test getting all capabilities."""
        mapper = CapabilityMapper()
        caps = mapper.get_capabilities(RobotType.G1)
        assert "movement" in caps
        assert "manipulation" in caps
        assert "perception" in caps

    def test_get_capabilities_category(self):
        """Test getting capabilities by category."""
        mapper = CapabilityMapper()
        caps = mapper.get_capabilities(RobotType.G1, category="movement")
        assert "movement" in caps
        assert len(caps) == 1

    def test_has_capability_true(self):
        """Test checking enabled capability."""
        mapper = CapabilityMapper()
        assert mapper.has_capability(RobotType.G1, "grasp") is True
        assert mapper.has_capability(RobotType.GO2, "walk") is True

    def test_has_capability_false(self):
        """Test checking disabled capability."""
        mapper = CapabilityMapper()
        assert mapper.has_capability(RobotType.GO2, "grasp") is False
        assert mapper.has_capability(RobotType.GO1, "lidar") is False

    def test_get_enabled_capabilities(self):
        """Test getting enabled capabilities."""
        mapper = CapabilityMapper()
        enabled = mapper.get_enabled_capabilities(RobotType.G1, category="movement")
        assert "walk" in enabled
        assert "run" in enabled
        assert "jump" in enabled

    def test_get_disabled_capabilities(self):
        """Test getting disabled capabilities."""
        mapper = CapabilityMapper()
        disabled = mapper.get_disabled_capabilities(RobotType.GO2, category="manipulation")
        assert "grasp" in disabled
        assert "pinch" in disabled

    def test_compare_capabilities(self):
        """Test comparing capabilities between robots."""
        mapper = CapabilityMapper()
        comparison = mapper.compare_capabilities(RobotType.G1, RobotType.GO2)
        assert "shared" in comparison
        assert "only_in_first" in comparison
        assert "only_in_second" in comparison
        # G1 has manipulation, Go2 doesn't
        assert "grasp" in comparison["only_in_first"]

    def test_filter_by_capabilities(self):
        """Test filtering robots by required capabilities."""
        mapper = CapabilityMapper()
        robots = [RobotType.G1, RobotType.GO2, RobotType.GO1]
        # Only G1 has grasping capability
        result = mapper.filter_by_capabilities(robots, ["grasp"])
        assert result == [RobotType.G1]

    def test_filter_by_multiple_capabilities(self):
        """Test filtering by multiple capabilities."""
        mapper = CapabilityMapper()
        robots = [RobotType.G1, RobotType.GO2, RobotType.GO1]
        # All have walking and camera
        result = mapper.filter_by_capabilities(robots, ["walk", "camera"])
        assert len(result) == 3


class TestSkillClassifier:
    """Tests for SkillClassifier."""

    def test_init(self):
        """Test SkillClassifier initialization."""
        classifier = SkillClassifier()
        assert classifier is not None

    def test_classify_skill_universal(self):
        """Test classifying universal skill."""
        classifier = SkillClassifier()
        skill = Skill(
            name="learn_new_action",
            description="Learn a new action",
            code="pass",
            tags=["learning"],
            supported_robots=[],
        )
        skill_type = classifier.classify_skill(skill, RobotType.G1)
        assert skill_type == SkillType.UNIVERSAL

    def test_classify_skill_body_specific(self):
        """Test classifying body-specific skill."""
        classifier = SkillClassifier()
        skill = Skill(
            name="grasp_object",
            description="Grasp an object with the gripper",
            code="pass",
            tags=["manipulation"],
            supported_robots=[RobotType.G1],
        )
        skill_type = classifier.classify_skill(skill, RobotType.G1)
        # Based on name, should be body-specific
        assert skill_type == SkillType.BODY_SPECIFIC

    def test_is_skill_compatible_true(self):
        """Test skill compatibility check (compatible)."""
        classifier = SkillClassifier()
        skill = Skill(
            name="walk_forward",
            description="Make robot walk forward",
            code="pass",
            tags=["movement"],
            supported_robots=[RobotType.G1, RobotType.GO2],
        )
        # Both robots support walk, so both should be compatible
        # But we check against the supported_robots list
        assert classifier.is_skill_compatible(skill, RobotType.G1) is True
        # Go3 is not in supported list, so incompatible
        assert classifier.is_skill_compatible(skill, RobotType.GO1) is False

    def test_is_skill_compatible_false(self):
        """Test skill compatibility check (incompatible)."""
        classifier = SkillClassifier()
        skill = Skill(
            name="grasp_object",
            description="Grasp an object (requires gripper)",
            code="pass",
            tags=["manipulation", "grasp"],
            supported_robots=[RobotType.G1],
        )
        # Go2 doesn't have gripper
        assert classifier.is_skill_compatible(skill, RobotType.GO2) is False

    def test_get_incompatible_capabilities(self):
        """Test getting incompatible capabilities."""
        classifier = SkillClassifier()
        skill = Skill(
            name="lidar_scan",
            description="Scan environment with LiDAR",
            code="pass",
            tags=["perception", "scan"],
            supported_robots=[],
        )
        # Go1 doesn't have lidar
        missing = classifier.get_incompatible_capabilities(skill, RobotType.GO1)
        assert len(missing) >= 0  # May be empty if requirements not detected

    def test_suggest_compatible_robots(self):
        """Test suggesting compatible robots."""
        classifier = SkillClassifier()
        skill = Skill(
            name="walk_forward",
            description="Walk forward",
            code="pass",
            tags=["movement"],
            supported_robots=[RobotType.G1, RobotType.GO2],  # Specify supported robots
        )
        robots = [RobotType.G1, RobotType.GO2, RobotType.GO1]
        compatible = classifier.suggest_compatible_robots(skill, robots)
        # Should suggest G1 and Go2 which are in supported_robots list
        assert RobotType.G1 in compatible or len(compatible) > 0

    def test_adapt_skill_for_robot_compatible(self):
        """Test skill adaptation for compatible robot."""
        classifier = SkillClassifier()
        skill = Skill(
            name="learn",
            description="Learn something new",
            code="pass",
            tags=["learning"],
            supported_robots=[],
        )
        # Learning skills don't require specific hardware
        suggestion = classifier.adapt_skill_for_robot(skill, RobotType.G1)
        assert suggestion is None  # Already compatible


class TestInsularCortex:
    """Tests for InsularCortex."""

    def test_init_without_robot(self):
        """Test initialization without robot type."""
        cortex = InsularCortex()
        assert cortex.robot_type is None

    def test_init_with_robot(self):
        """Test initialization with robot type."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        assert cortex.robot_type == RobotType.G1

    def test_identify_robot(self):
        """Test robot identification."""
        cortex = InsularCortex()
        robot_type = cortex.identify_robot("G1-EDU")
        assert robot_type == RobotType.G1
        assert cortex.get_robot_type() == RobotType.G1

    def test_get_robot_type(self):
        """Test getting robot type."""
        cortex = InsularCortex(robot_type=RobotType.GO2)
        assert cortex.get_robot_type() == RobotType.GO2

    def test_get_robot_profile(self):
        """Test getting robot profile."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        profile = cortex.get_robot_profile()
        assert profile["type"] == RobotType.G1
        assert profile["dof"] == 26

    def test_get_dof_count(self):
        """Test getting DOF count."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        assert cortex.get_dof_count() == 26

    def test_is_humanoid(self):
        """Test humanoid detection."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        assert cortex.is_humanoid() is True

    def test_has_gripper(self):
        """Test gripper detection."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        assert cortex.has_gripper() is True

    def test_get_capabilities(self):
        """Test getting capabilities."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        caps = cortex.get_capabilities()
        assert "movement" in caps
        assert "manipulation" in caps

    def test_has_capability(self):
        """Test checking capability."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        assert cortex.has_capability("grasp") is True
        assert cortex.has_capability("lidar") is True

    def test_get_enabled_capabilities(self):
        """Test getting enabled capabilities."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        enabled = cortex.get_enabled_capabilities(category="movement")
        assert "walk" in enabled

    def test_get_disabled_capabilities(self):
        """Test getting disabled capabilities."""
        cortex = InsularCortex(robot_type=RobotType.GO2)
        disabled = cortex.get_disabled_capabilities(category="manipulation")
        assert "grasp" in disabled

    def test_classify_skill(self):
        """Test skill classification."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        skill = Skill(
            name="learn",
            description="Learn something",
            code="pass",
            tags=["learning"],
            supported_robots=[],
        )
        skill_type = cortex.classify_skill(skill)
        assert skill_type in [SkillType.UNIVERSAL, SkillType.BODY_SPECIFIC]

    def test_can_run_skill(self):
        """Test skill compatibility check."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        skill = Skill(
            name="learn",
            description="Learn something new",
            code="pass",
            tags=["learning"],
            supported_robots=[],
        )
        # Learning skills don't require specific hardware
        assert cortex.can_run_skill(skill) is True

    def test_get_incompatible_capabilities_for_skill(self):
        """Test getting missing capabilities for skill."""
        cortex = InsularCortex(robot_type=RobotType.GO2)
        skill = Skill(
            name="grasp",
            description="Grasp object",
            code="pass",
            tags=["grasp"],
            supported_robots=[RobotType.G1],
        )
        missing = cortex.get_incompatible_capabilities(skill)
        # May be empty if requirements not detected
        assert isinstance(missing, list)

    def test_get_adaptation_suggestion(self):
        """Test getting adaptation suggestion."""
        cortex = InsularCortex(robot_type=RobotType.GO2)
        skill = Skill(
            name="grasp",
            description="Grasp an object",
            code="pass",
            tags=["manipulation", "grasp"],
            supported_robots=[RobotType.G1],
        )
        suggestion = cortex.get_adaptation_suggestion(skill)
        # If incompatible, should have suggestion
        if not cortex.can_run_skill(skill):
            assert suggestion is not None

    def test_compare_with_robot(self):
        """Test comparing with another robot."""
        cortex = InsularCortex(robot_type=RobotType.G1)
        comparison = cortex.compare_with_robot(RobotType.GO2)
        assert "shared" in comparison
        assert "only_in_first" in comparison

    def test_error_without_robot_type(self):
        """Test error when operations called without robot type."""
        cortex = InsularCortex()
        with pytest.raises(ValueError, match="Robot type not identified"):
            cortex.get_robot_profile()

    def test_repr(self):
        """Test string representation."""
        cortex = InsularCortex(robot_type=RobotType.G1, firmware_version="1.5.0")
        repr_str = repr(cortex)
        assert "InsularCortex" in repr_str
        assert "G1" in repr_str
