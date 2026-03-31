"""
Core type definitions for the Self-Evolving Robot System.
Based on neuroscience-inspired brain structure.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID, uuid4


# ============================================================================
# Enumerations
# ============================================================================

class RobotType(str, Enum):
    """Supported robot types."""
    G1 = "G1"
    G1_EDU = "G1-EDU"
    GO2 = "Go2"
    GO2_EDU = "Go2-EDU"
    GO1 = "Go1"
    B1 = "B1"


class SkillStatus(str, Enum):
    """Status of a skill."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"
    DRAFT = "draft"


class DangerLevel(str, Enum):
    """Safety assessment levels."""
    GREEN = "green"      # Safe to execute
    YELLOW = "yellow"    # Requires confirmation
    RED = "red"          # Dangerous, refuse


class SkillType(str, Enum):
    """Classification of skills."""
    UNIVERSAL = "universal"        # Works on all robots
    BODY_SPECIFIC = "body_specific" # Specific to robot type
    HYBRID = "hybrid"              # Partially universal


class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class SandboxType(str, Enum):
    """Execution sandbox types for code safety."""
    RESTRICTED_PYTHON = "restricted_python"  # RestrictedPython with AST analysis
    DOCKER = "docker"                        # Docker container isolation
    PROCESS = "process"                      # Isolated subprocess with timeout
    DISABLED = "disabled"                    # No sandbox (development only)


# ============================================================================
# Core Data Structures
# ============================================================================

@dataclass
class Intent:
    """Parsed user intent from conversation."""
    raw_text: str
    action: str  # e.g., "move", "grasp", "learn"
    parameters: Dict[str, Any]
    confidence: float
    constraints: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Subtask:
    """A decomposed subtask from a user intent."""
    intent: Intent
    task_id: str = field(default_factory=lambda: str(uuid4()))
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RobotProfile:
    """Profile of a specific robot instance."""
    robot_type: RobotType
    body_id: str  # Unique identifier for this specific robot
    capabilities: Dict[str, Any]  # e.g., {"max_speed": 2.0, "joints": 12}
    firmware_version: str
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Skill:
    """A reusable skill/capability."""
    name: str
    description: str
    code: str  # Python code
    skill_id: str = field(default_factory=lambda: str(uuid4()))
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    supported_robots: List[RobotType] = field(default_factory=list)
    status: SkillStatus = SkillStatus.DRAFT
    skill_type: SkillType = SkillType.UNIVERSAL
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    last_modified: datetime = field(default_factory=datetime.now)
    
    # Performance metrics
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    version: int = 1
    
    # Adaptation
    adaptations: Dict[RobotType, str] = field(default_factory=dict)  # robot-specific code variants


@dataclass
class UserProfile:
    """Profile of a user."""
    user_id: str = field(default_factory=lambda: str(uuid4()))
    name: Optional[str] = None
    face_embedding: Optional[List[float]] = None  # Vector representation of face
    preferences: Dict[str, Any] = field(default_factory=dict)
    interaction_history: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)


@dataclass
class SensorData:
    """Current sensor readings from robot."""
    timestamp: datetime = field(default_factory=datetime.now)
    lidar_data: Optional[List[float]] = None  # Distance readings
    camera_data: Optional[bytes] = None  # Image data
    joint_angles: Optional[List[float]] = None
    velocity: Optional[List[float]] = None
    battery_level: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """An action to be executed on the robot."""
    action_type: str  # e.g., "move_forward", "turn", "grab"
    parameters: Dict[str, Any]
    action_id: str = field(default_factory=lambda: str(uuid4()))
    timeout: float = 30.0  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SafetyAssessment:
    """Safety assessment result."""
    action: Action
    danger_level: DangerLevel
    reason: str
    suggestions: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    user_input: str
    turn_id: str = field(default_factory=lambda: str(uuid4()))
    user_image: Optional[bytes] = None
    robot_response: str = ""
    intents: List[Intent] = field(default_factory=list)
    actions_taken: List[Action] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningRecord:
    """Record of a learned skill."""
    skill_id: str
    robot_type: RobotType
    learning_date: datetime
    trials: int
    successes: int
    failures: int
    performance_metric: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RobotCapabilities:
    """Capabilities of a robot."""
    robot_type: RobotType
    max_speed: float
    joint_count: int
    has_gripper: bool
    has_camera: bool
    has_lidar: bool
    supported_skills: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillPackage:
    """Package for sharing skills between robots."""
    skill: Skill
    metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source_robot_id: Optional[str] = None


@dataclass
class CodeExecutionPolicy:
    """Security policy for code execution."""
    sandbox_type: 'SandboxType' = SandboxType.RESTRICTED_PYTHON
    timeout: float = 60.0  # seconds
    max_memory: Optional[int] = None  # MB
    allowed_imports: List[str] = field(default_factory=lambda: [
        "math", "random", "time", "collections", "itertools"
    ])
    forbidden_modules: List[str] = field(default_factory=lambda: [
        "os", "sys", "subprocess", "socket", "threading", "multiprocessing"
    ])
    forbidden_builtins: List[str] = field(default_factory=lambda: [
        "exec", "eval", "compile", "__import__", "open", "input"
    ])
    enable_network: bool = False
    enable_file_access: bool = False
    enable_subprocess: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationContext:
    """Context maintained during conversation."""
    current_user: Optional[UserProfile] = None
    current_robot: Optional[RobotProfile] = None
    conversation_history: List[ConversationTurn] = field(default_factory=list)
    current_task: Optional[Subtask] = None
    sensor_data: Optional[SensorData] = None
    last_update: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Interfaces/Protocols
# ============================================================================

@dataclass
class IntentResult:
    """Result of intent parsing."""
    intents: List[Intent]
    confidence: float
    context: ConversationContext


@dataclass
class RobotContext:
    """Context for robot operations."""
    robot_profile: RobotProfile
    current_sensor_data: SensorData
    skill_library: Dict[str, Skill]
    safety_constraints: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SceneInfo:
    """Information about the scene from vision."""
    objects_detected: List[Dict[str, Any]]
    obstacles: List[Dict[str, Any]]
    layout_description: str
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
