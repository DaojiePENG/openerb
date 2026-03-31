"""
Test core storage functionality.
"""

import pytest
from datetime import datetime
from openerb.core import (
    Skill, SkillStatus, SkillType, RobotType, UserProfile,
    Intent, Subtask, TaskStatus, SensorData, Action, SafetyAssessment,
    DangerLevel, ExecutionResult, ConversationTurn, RobotProfile,
    LearningRecord, RobotCapabilities, SkillPackage, CodeExecutionPolicy,
    SandboxType, ConversationContext, IntentResult, RobotContext, SceneInfo,
)


class TestStorage:
    """Tests for the Storage class."""
    
    def test_skill_save_and_load(self, test_storage, test_skill):
        """Test saving and loading a skill."""
        # Save
        assert test_storage.save_skill(test_skill)
        
        # Load
        loaded = test_storage.load_skill(test_skill.skill_id)
        assert loaded is not None
        assert loaded.name == test_skill.name
        assert loaded.skill_id == test_skill.skill_id
        assert loaded.code == test_skill.code
    
    def test_skill_not_found(self, test_storage):
        """Test loading non-existent skill."""
        loaded = test_storage.load_skill("non_existent_skill_id")
        assert loaded is None
    
    def test_list_skills(self, test_storage, test_skill):
        """Test listing skills."""
        # Save multiple skills
        test_storage.save_skill(test_skill)
        
        skill2 = Skill(
            name="test_grab",
            description="Test grasping",
            code="print('Grabbing')",
            status=SkillStatus.ACTIVE,
            skill_type=SkillType.UNIVERSAL,
        )
        test_storage.save_skill(skill2)
        
        # List all
        all_skills = test_storage.list_skills()
        assert len(all_skills) >= 2
        
        # List by status
        active_skills = test_storage.list_skills("active")
        assert len(active_skills) >= 2
    
    def test_skill_update(self, test_storage, test_skill):
        """Test updating a skill."""
        test_storage.save_skill(test_skill)
        
        # Update skill
        test_skill.success_count = 10
        test_skill.failure_count = 2
        test_skill.version = 2
        assert test_storage.save_skill(test_skill)
        
        # Verify update
        loaded = test_storage.load_skill(test_skill.skill_id)
        assert loaded.version == 2
        assert loaded.success_count == 10
    
    def test_robot_profile_save_and_load(self, test_storage, test_robot_profile):
        """Test saving and loading robot profile."""
        # Save
        assert test_storage.save_robot_profile(test_robot_profile)
        
        # Load
        loaded = test_storage.load_robot_profile(test_robot_profile.body_id)
        assert loaded is not None
        assert loaded.robot_type == test_robot_profile.robot_type
        assert loaded.body_id == test_robot_profile.body_id
    
    def test_robot_profile_not_found(self, test_storage):
        """Test loading non-existent robot profile."""
        loaded = test_storage.load_robot_profile("non_existent_body_id")
        assert loaded is None
    
    def test_robot_profile_update(self, test_storage, test_robot_profile):
        """Test updating a robot profile."""
        test_storage.save_robot_profile(test_robot_profile)
        
        # Update profile
        test_robot_profile.capabilities["max_speed"] = 3.0
        assert test_storage.save_robot_profile(test_robot_profile)
        
        # Verify update
        loaded = test_storage.load_robot_profile(test_robot_profile.body_id)
        assert loaded.capabilities["max_speed"] == 3.0
    
    def test_user_profile_save_and_load(self, test_storage, test_user_profile):
        """Test saving and loading user profile."""
        # Save
        assert test_storage.save_user_profile(test_user_profile)
        
        # Load
        loaded = test_storage.load_user_profile(test_user_profile.user_id)
        assert loaded is not None
        assert loaded.name == test_user_profile.name
        assert loaded.user_id == test_user_profile.user_id
    
    def test_user_profile_not_found(self, test_storage):
        """Test loading non-existent user profile."""
        loaded = test_storage.load_user_profile("non_existent_user_id")
        assert loaded is None


class TestTypes:
    """Tests for type definitions."""
    
    def test_skill_success_rate_calculation(self, test_skill):
        """Test skill success rate."""
        test_skill.success_count = 8
        test_skill.failure_count = 2
        test_skill.success_rate = (
            test_skill.success_count /
            (test_skill.success_count + test_skill.failure_count)
        )
        
        assert test_skill.success_rate == 0.8
    
    def test_robot_type_enum(self):
        """Test RobotType enum."""
        assert RobotType.G1.value == "G1"
        assert RobotType.GO2.value == "Go2"
        assert str(RobotType.G1) == "RobotType.G1"
        # Test all robot types
        assert RobotType.G1_EDU.value == "G1-EDU"
        assert RobotType.GO2_EDU.value == "Go2-EDU"
        assert RobotType.GO1.value == "Go1"
        assert RobotType.B1.value == "B1"
    
    def test_skill_status_enum(self):
        """Test SkillStatus enum."""
        assert SkillStatus.ACTIVE.value == "active"
        assert SkillStatus.DEPRECATED.value == "deprecated"
        assert SkillStatus.RETIRED.value == "retired"
        assert SkillStatus.DRAFT.value == "draft"
    
    def test_danger_level_enum(self):
        """Test DangerLevel enum."""
        assert DangerLevel.GREEN.value == "green"
        assert DangerLevel.YELLOW.value == "yellow"
        assert DangerLevel.RED.value == "red"
    
    def test_skill_type_enum(self):
        """Test SkillType enum."""
        assert SkillType.UNIVERSAL.value == "universal"
        assert SkillType.BODY_SPECIFIC.value == "body_specific"
        assert SkillType.HYBRID.value == "hybrid"
    
    def test_task_status_enum(self):
        """Test TaskStatus enum."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.REJECTED.value == "rejected"
    
    def test_sandbox_type_enum(self):
        """Test SandboxType enum."""
        assert SandboxType.RESTRICTED_PYTHON.value == "restricted_python"
        assert SandboxType.DOCKER.value == "docker"
        assert SandboxType.PROCESS.value == "process"
        assert SandboxType.DISABLED.value == "disabled"
    
    def test_intent_creation(self):
        """Test Intent dataclass creation."""
        intent = Intent(
            raw_text="Move forward 1 meter",
            action="move",
            parameters={"distance": 1.0, "direction": "forward"},
            confidence=0.95,
        )
        assert intent.raw_text == "Move forward 1 meter"
        assert intent.action == "move"
        assert intent.confidence == 0.95
        assert intent.constraints == {}
    
    def test_subtask_creation(self):
        """Test Subtask dataclass creation."""
        intent = Intent(
            raw_text="Test",
            action="test",
            parameters={},
            confidence=1.0,
        )
        subtask = Subtask(
            intent=intent,
            priority=1,
            dependencies=["task1"],
        )
        assert subtask.priority == 1
        assert subtask.status == TaskStatus.PENDING
        assert len(subtask.dependencies) == 1
    
    def test_sensor_data_creation(self):
        """Test SensorData dataclass creation."""
        sensor_data = SensorData(
            lidar_data=[1.0, 2.0, 3.0],
            camera_data=b"image_data",
            joint_angles=[0.0, 1.57, 3.14],
            velocity=[0.5, 0.0, 0.0],
            battery_level=0.85,
        )
        assert sensor_data.lidar_data == [1.0, 2.0, 3.0]
        assert sensor_data.battery_level == 0.85
    
    def test_action_creation(self):
        """Test Action dataclass creation."""
        action = Action(
            action_type="move_forward",
            parameters={"distance": 1.0, "speed": 0.5},
            timeout=30.0,
        )
        assert action.action_type == "move_forward"
        assert action.timeout == 30.0
    
    def test_safety_assessment_creation(self):
        """Test SafetyAssessment dataclass creation."""
        action = Action(
            action_type="move_forward",
            parameters={"distance": 1.0},
        )
        assessment = SafetyAssessment(
            action=action,
            danger_level=DangerLevel.GREEN,
            reason="Area is clear",
            suggestions=["Proceed with caution"],
        )
        assert assessment.danger_level == DangerLevel.GREEN
        assert assessment.reason == "Area is clear"
    
    def test_execution_result_creation(self):
        """Test ExecutionResult dataclass creation."""
        result = ExecutionResult(
            success=True,
            output="Task completed successfully",
            execution_time=0.5,
        )
        assert result.success is True
        assert result.execution_time == 0.5
        assert result.error is None
    
    def test_conversation_turn_creation(self):
        """Test ConversationTurn dataclass creation."""
        turn = ConversationTurn(
            user_input="Move forward",
            robot_response="Moving forward now",
        )
        assert turn.user_input == "Move forward"
        assert turn.robot_response == "Moving forward now"
        assert turn.user_image is None
    
    def test_learning_record_creation(self):
        """Test LearningRecord dataclass creation."""
        record = LearningRecord(
            skill_id="skill_001",
            robot_type=RobotType.G1,
            learning_date=datetime.now(),
            trials=10,
            successes=8,
            failures=2,
            performance_metric=0.8,
        )
        assert record.skill_id == "skill_001"
        assert record.robot_type == RobotType.G1
        assert record.trials == 10
    
    def test_robot_capabilities_creation(self):
        """Test RobotCapabilities dataclass creation."""
        caps = RobotCapabilities(
            robot_type=RobotType.G1,
            max_speed=2.0,
            joint_count=12,
            has_gripper=True,
            has_camera=True,
            has_lidar=True,
        )
        assert caps.robot_type == RobotType.G1
        assert caps.max_speed == 2.0
        assert caps.has_gripper is True
    
    def test_skill_package_creation(self):
        """Test SkillPackage dataclass creation."""
        skill = Skill(
            name="test_skill",
            description="A test skill",
            code="print('test')",
        )
        package = SkillPackage(
            skill=skill,
            metadata={"version": "1.0"},
            source_robot_id="G1_001",
        )
        assert package.skill.name == "test_skill"
        assert package.source_robot_id == "G1_001"
    
    def test_code_execution_policy_creation(self):
        """Test CodeExecutionPolicy dataclass creation."""
        policy = CodeExecutionPolicy(
            sandbox_type=SandboxType.RESTRICTED_PYTHON,
            timeout=60.0,
            enable_network=False,
            enable_file_access=False,
        )
        assert policy.sandbox_type == SandboxType.RESTRICTED_PYTHON
        assert policy.timeout == 60.0
        assert policy.enable_network is False
        assert "os" in policy.forbidden_modules
    
    def test_conversation_context_creation(self):
        """Test ConversationContext dataclass creation."""
        context = ConversationContext()
        assert context.current_user is None
        assert context.current_robot is None
        assert len(context.conversation_history) == 0
    
    def test_intent_result_creation(self):
        """Test IntentResult dataclass creation."""
        intent = Intent(
            raw_text="Test",
            action="test",
            parameters={},
            confidence=1.0,
        )
        context = ConversationContext()
        result = IntentResult(
            intents=[intent],
            confidence=0.95,
            context=context,
        )
        assert len(result.intents) == 1
        assert result.confidence == 0.95
    
    def test_robot_context_creation(self):
        """Test RobotContext dataclass creation."""
        profile = RobotProfile(
            robot_type=RobotType.G1,
            body_id="G1_001",
            capabilities={},
            firmware_version="1.0.0",
        )
        sensor_data = SensorData()
        context = RobotContext(
            robot_profile=profile,
            current_sensor_data=sensor_data,
            skill_library={},
            safety_constraints={},
        )
        assert context.robot_profile.body_id == "G1_001"
    
    def test_scene_info_creation(self):
        """Test SceneInfo dataclass creation."""
        scene = SceneInfo(
            objects_detected=[{"type": "person", "confidence": 0.9}],
            obstacles=[{"type": "wall", "distance": 1.5}],
            layout_description="Indoor corridor",
            confidence=0.85,
        )
        assert len(scene.objects_detected) == 1
        assert len(scene.obstacles) == 1
        assert scene.layout_description == "Indoor corridor"
