"""
Test configuration and fixtures.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    SystemConfig, APIConfig, RobotConfig, StorageConfig, LoggingConfig,
    set_config, set_storage, Storage,
    Skill, SkillStatus, SkillType, RobotProfile, RobotType, UserProfile
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_storage(temp_dir):
    """Create a test storage instance."""
    storage_config = StorageConfig(
        data_dir=temp_dir / "data",
        skills_dir=temp_dir / "skills",
        generated_code_dir=temp_dir / "generated_code",
        logs_dir=temp_dir / "logs",
        db_path=temp_dir / "test.db",
    )
    
    config = SystemConfig(
        api=APIConfig(),
        robot=RobotConfig(),
        storage=storage_config,
        logging=LoggingConfig(),
    )
    
    set_config(config)
    storage = Storage(db_path=storage_config.db_path)
    set_storage(storage)
    
    return storage


@pytest.fixture
def test_skill():
    """Create a test skill."""
    return Skill(
        name="test_move",
        description="Test movement skill",
        code="print('Moving')",
        tags=["movement", "test"],
        supported_robots=[RobotType.G1, RobotType.GO2],
        status=SkillStatus.ACTIVE,
        skill_type=SkillType.UNIVERSAL,
    )


@pytest.fixture
def test_robot_profile():
    """Create a test robot profile."""
    return RobotProfile(
        robot_type=RobotType.G1,
        body_id="G1_001",
        firmware_version="1.0.0",
        capabilities={
            "max_speed": 2.0,
            "joints": 12,
            "has_gripper": True,
        }
    )


@pytest.fixture
def test_user_profile():
    """Create a test user profile."""
    return UserProfile(
        name="Test User",
        face_embedding=[0.1] * 128,
        preferences={"preferred_speed": "normal"}
    )
