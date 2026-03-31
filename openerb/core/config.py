"""
Configuration management for the Self-Evolving Robot System.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


@dataclass
class APIConfig:
    """Configuration for external APIs."""
    dashscope_api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    dashscope_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    dashscope_model: str = "qwen-vl-plus"
    
    # Fallback LLM config
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = "gpt-4-vision"


@dataclass
class RobotConfig:
    """Configuration for robot control."""
    robot_type: str = "G1"  # Default robot type
    body_id: Optional[str] = None  # Will be auto-detected
    sdk_path: Optional[str] = None  # Path to Unitree SDK
    control_timeout: float = 30.0  # seconds
    motion_enabled: bool = True
    safety_strict_mode: bool = True


@dataclass
class StorageConfig:
    """Configuration for data storage."""
    data_dir: Path = Path.home() / "robot_self_control" / "data"
    skills_dir: Path = Path.home() / "robot_self_control" / "skills"
    generated_code_dir: Path = Path.home() / "robot_self_control" / "generated_code"
    logs_dir: Path = Path.home() / "robot_self_control" / "logs"
    db_path: Path = Path.home() / "robot_self_control" / "data" / "robot.db"
    
    def ensure_directories(self):
        """Create all necessary directories."""
        for directory in [self.data_dir, self.skills_dir, self.generated_code_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    log_level: str = "INFO"
    log_file: Optional[str] = None
    console_output: bool = True
    log_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"


@dataclass
class SystemConfig:
    """Main system configuration."""
    api: APIConfig
    robot: RobotConfig
    storage: StorageConfig
    logging: LoggingConfig
    
    # Global settings
    debug_mode: bool = os.getenv("DEBUG", "False").lower() == "true"
    code_execution_timeout: float = 60.0  # seconds
    max_code_length: int = 10000  # characters
    
    def __post_init__(self):
        """Initialize directories after instantiation."""
        self.storage.ensure_directories()
    
    @classmethod
    def from_env(cls) -> "SystemConfig":
        """Create config from environment variables."""
        return cls(
            api=APIConfig(),
            robot=RobotConfig(
                robot_type=os.getenv("ROBOT_TYPE", "G1"),
                body_id=os.getenv("ROBOT_BODY_ID"),
            ),
            storage=StorageConfig(),
            logging=LoggingConfig(
                log_level=os.getenv("LOG_LEVEL", "INFO"),
            ),
            debug_mode=os.getenv("DEBUG", "False").lower() == "true",
        )


# Global config instance
_global_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """Get the global system configuration."""
    global _global_config
    if _global_config is None:
        _global_config = SystemConfig.from_env()
    return _global_config


def set_config(config: SystemConfig) -> None:
    """Set the global system configuration."""
    global _global_config
    _global_config = config


# Convenience functions
def get_api_config() -> APIConfig:
    """Get API configuration."""
    return get_config().api


def get_robot_config() -> RobotConfig:
    """Get robot configuration."""
    return get_config().robot


def get_storage_config() -> StorageConfig:
    """Get storage configuration."""
    return get_config().storage


def get_logging_config() -> LoggingConfig:
    """Get logging configuration."""
    return get_config().logging
