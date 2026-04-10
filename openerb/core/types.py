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
class CommunicationNode:
    """Robot network node for communication between agents."""
    node_id: str
    robot_type: RobotType
    address: str
    capabilities: Dict[str, Any] = field(default_factory=dict)
    last_seen: datetime = field(default_factory=datetime.now)


@dataclass
class Message:
    """Message packet for robot communication."""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExperienceReport:
    """Report from a robot of skill performance and environment signals."""
    node_id: str
    skill_id: str
    success: bool
    duration_ms: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CollaborationPolicy:
    """Configuration for distributed communication and learning."""
    max_concurrent_transfers: int = 5
    bandwidth_limit_mbps: float = 10.0
    trust_threshold: float = 0.7
    enable_encryption: bool = True
    allowed_robot_types: List[RobotType] = field(default_factory=lambda: [RobotType.G1, RobotType.G1_EDU, RobotType.GO1, RobotType.GO2, RobotType.GO2_EDU])
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeExecutionPolicy:
    """Security policy for code execution."""
    sandbox_type: 'SandboxType' = SandboxType.RESTRICTED_PYTHON
    timeout: float = 60.0  # seconds
    max_memory: Optional[int] = None  # MB
    allowed_imports: List[str] = field(default_factory=lambda: [
        "math", "random", "time", "collections", "itertools",
        "matplotlib", "numpy", "pathlib",
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


# ============================================================================
# Visual Cortex Types - Phase 4.1
# ============================================================================

class ImageFormat(str, Enum):
    """Supported image formats."""
    RGB = "rgb"
    BGR = "bgr"
    RGBA = "rgba"
    GRAYSCALE = "grayscale"


class ObjectCategory(str, Enum):
    """Common object categories for detection."""
    PERSON = "person"
    ROBOT = "robot"
    OBSTACLE = "obstacle"
    TOOL = "tool"
    FURNITURE = "furniture"
    UNKNOWN = "unknown"


class FaceAttribute(str, Enum):
    """Recognized face attributes."""
    GENDER = "gender"
    AGE_GROUP = "age_group"
    EMOTION = "emotion"
    POSE = "pose"


@dataclass
class BoundingBox:
    """Bounding box for object detection."""
    x: float  # Top-left x coordinate (0-1, normalized)
    y: float  # Top-left y coordinate (0-1, normalized)
    width: float  # Width (0-1, normalized)
    height: float  # Height (0-1, normalized)
    confidence: float  # Detection confidence (0-1)
    
    def to_pixels(self, image_width: int, image_height: int) -> Dict[str, int]:
        """Convert normalized coordinates to pixel coordinates."""
        return {
            "x": int(self.x * image_width),
            "y": int(self.y * image_height),
            "width": int(self.width * image_width),
            "height": int(self.height * image_height),
        }


@dataclass
class DetectedObject:
    """Detected object in an image."""
    object_id: str = field(default_factory=lambda: str(uuid4()))
    category: ObjectCategory = ObjectCategory.UNKNOWN
    label: str = ""  # Specific object name
    bbox: Optional[BoundingBox] = None
    confidence: float = 0.0
    color: Optional[str] = None
    features: Dict[str, Any] = field(default_factory=dict)  # Color, texture, etc.
    embedding: Optional[List[float]] = None  # Feature vector for similarity
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FaceDetection:
    """Detected face in an image."""
    face_id: str = field(default_factory=lambda: str(uuid4()))
    bbox: Optional[BoundingBox] = None
    face_embedding: Optional[List[float]] = None  # 128-D or 256-D encoding
    confidence: float = 0.0
    attributes: Dict[FaceAttribute, Any] = field(default_factory=dict)
    identified_user: Optional[UserProfile] = None  # If recognized
    identification_confidence: float = 0.0
    landmarks: Dict[str, tuple] = field(default_factory=dict)  # Facial landmarks
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ImageAnnotation:
    """Annotated image with detected objects and faces."""
    image_id: str = field(default_factory=lambda: str(uuid4()))
    image_bytes: Optional[bytes] = None  # Original image data
    image_width: int = 0
    image_height: int = 0
    format: ImageFormat = ImageFormat.RGB
    
    # Detection results
    objects: List[DetectedObject] = field(default_factory=list)
    faces: List[FaceDetection] = field(default_factory=list)
    
    # High-level understanding
    scene_description: str = ""
    main_objects: List[str] = field(default_factory=list)
    spatial_layout: str = ""
    
    # Processing metadata
    processing_time: float = 0.0  # ms
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Relationship:
    """Spatial relationship between two objects."""
    object1_id: str
    object2_id: str
    relation_type: str  # "left_of", "above", "near", "behind", etc.
    distance: float = 0.0  # Estimated distance (meters)
    confidence: float = 0.0


@dataclass
class SpatialLayout:
    """Spatial understanding of the scene."""
    layout_id: str = field(default_factory=lambda: str(uuid4()))
    objects: List[DetectedObject] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    estimated_distances: Dict[str, float] = field(default_factory=dict)  # object_id -> distance
    depth_map: Optional[List[List[float]]] = None  # Depth estimation
    robot_position: Optional[tuple] = None  # (x, y, z) in scene coordinates
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VisualAnalysisResult:
    """Complete result of visual analysis."""
    annotation: ImageAnnotation
    spatial_layout: Optional[SpatialLayout] = None
    recognized_users: List[UserProfile] = field(default_factory=list)
    analysis_confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
