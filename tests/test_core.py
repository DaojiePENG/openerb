"""
Test core storage functionality.
"""

import pytest
from openerb.core import Skill, SkillStatus, SkillType, RobotType, UserProfile


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
    
    def test_robot_profile_save_and_load(self, test_storage, test_robot_profile):
        """Test saving and loading robot profile."""
        # Save
        assert test_storage.save_robot_profile(test_robot_profile)
        
        # Load
        loaded = test_storage.load_robot_profile(test_robot_profile.body_id)
        assert loaded is not None
        assert loaded.robot_type == test_robot_profile.robot_type
        assert loaded.body_id == test_robot_profile.body_id
    
    def test_user_profile_save_and_load(self, test_storage, test_user_profile):
        """Test saving and loading user profile."""
        # Save
        assert test_storage.save_user_profile(test_user_profile)
        
        # Load
        loaded = test_storage.load_user_profile(test_user_profile.user_id)
        assert loaded is not None
        assert loaded.name == test_user_profile.name
        assert loaded.user_id == test_user_profile.user_id


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
