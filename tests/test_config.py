"""
Test configuration system.
"""

import pytest
from pathlib import Path
from core import (
    SystemConfig, APIConfig, RobotConfig, StorageConfig, LoggingConfig,
    set_config, get_config,
)


class TestAPIConfig:
    """Tests for APIConfig."""
    
    def test_api_config_defaults(self):
        """Test APIConfig default values."""
        config = APIConfig()
        assert config.dashscope_api_base is not None
        assert "dashscope" in config.dashscope_api_base.lower()
        assert config.dashscope_model == "qwen-vl-plus"
    
    def test_api_config_custom(self):
        """Test APIConfig with custom values."""
        config = APIConfig(
            dashscope_api_key="test_key",
            dashscope_api_base="https://test.api.com",
        )
        assert config.dashscope_api_key == "test_key"
        assert config.dashscope_api_base == "https://test.api.com"


class TestRobotConfig:
    """Tests for RobotConfig."""
    
    def test_robot_config_defaults(self):
        """Test RobotConfig default values."""
        config = RobotConfig()
        assert config.robot_type == "G1"
        assert config.control_timeout > 0
        assert config.motion_enabled is True


class TestStorageConfig:
    """Tests for StorageConfig."""
    
    def test_storage_config_creation(self, temp_dir):
        """Test StorageConfig creation."""
        config = StorageConfig(
            data_dir=temp_dir / "data",
            skills_dir=temp_dir / "skills",
            generated_code_dir=temp_dir / "generated_code",
            logs_dir=temp_dir / "logs",
            db_path=temp_dir / "test.db",
        )
        assert config.data_dir == temp_dir / "data"
        assert config.skills_dir == temp_dir / "skills"
        assert config.db_path == temp_dir / "test.db"
    
    def test_storage_config_defaults(self, temp_dir):
        """Test StorageConfig with defaults."""
        config = StorageConfig(db_path=temp_dir / "default.db")
        assert config.db_path == temp_dir / "default.db"


class TestLoggingConfig:
    """Tests for LoggingConfig."""
    
    def test_logging_config_defaults(self):
        """Test LoggingConfig default values."""
        config = LoggingConfig()
        assert config.log_level == "INFO"
        assert config.console_output is True


class TestSystemConfig:
    """Tests for SystemConfig."""
    
    def test_system_config_creation(self, temp_dir):
        """Test SystemConfig creation."""
        config = SystemConfig(
            api=APIConfig(),
            robot=RobotConfig(),
            storage=StorageConfig(db_path=temp_dir / "test.db"),
            logging=LoggingConfig(),
        )
        assert config.api is not None
        assert config.robot is not None
        assert config.storage is not None
        assert config.logging is not None
    
    def test_config_get_set(self, temp_dir):
        """Test setting and getting global config."""
        config = SystemConfig(
            api=APIConfig(dashscope_api_key="test_key"),
            robot=RobotConfig(),
            storage=StorageConfig(db_path=temp_dir / "test.db"),
            logging=LoggingConfig(),
        )
        set_config(config)
        retrieved = get_config()
        assert retrieved is not None
        assert retrieved.api.dashscope_api_key == "test_key"
