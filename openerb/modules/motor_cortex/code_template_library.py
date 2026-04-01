"""Code template library for Motor Cortex - Predefined skill templates for code generation."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from openerb.core.types import RobotType, SkillType

logger = logging.getLogger(__name__)


@dataclass
class CodeTemplate:
    """A reusable code template for skill generation."""
    template_id: str
    name: str
    description: str
    category: str  # e.g., "movement", "manipulation", "perception"
    template_code: str
    placeholders: List[str] = field(default_factory=list)  # e.g., ["distance", "speed"]
    required_imports: List[str] = field(default_factory=list)
    supported_robots: List[RobotType] = field(default_factory=list)
    skill_type: SkillType = SkillType.UNIVERSAL
    tags: List[str] = field(default_factory=list)
    examples: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CodeTemplateLibrary:
    """Library of code templates for different robot skills."""
    
    def __init__(self):
        """Initialize template library with predefined templates."""
        self.templates: Dict[str, CodeTemplate] = {}
        self.categories: Dict[str, List[str]] = {}  # Category -> template IDs
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default templates for common skills."""
        
        # Movement templates
        
        # 1. Simple move forward
        self.register_template(CodeTemplate(
            template_id="move_forward",
            name="Move Forward",
            description="Make robot move forward a certain distance",
            category="movement",
            template_code="""# Move forward
import time
from unitree_sdk_interface import MotionController

def move_forward(distance: float = 0.5, speed: float = 0.5, timeout: float = 10.0) -> Dict[str, Any]:
    '''
    Move robot forward.
    
    Args:
        distance: Distance to move in meters (default: 0.5)
        speed: Movement speed (0.0-1.0) (default: 0.5)
        timeout: Operation timeout in seconds (default: 10.0)
    
    Returns:
        Dict with success status and execution details
    '''
    try:
        controller = MotionController()
        
        # Calculate velocity and duration
        velocity = speed * 1.0  # Max speed ~1.0 m/s
        duration = distance / velocity if velocity > 0 else 0
        
        # Execute movement
        result = controller.move_forward(velocity, duration)
        
        if result.get("success"):
            return {
                "success": True,
                "distance_moved": distance,
                "time_taken": min(duration, timeout),
                "status": "completed"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Movement failed"),
                "status": "failed"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "error"
        }

# Execute
result = move_forward(distance={distance}, speed={speed})
return result
""",
            placeholders=["distance", "speed"],
            required_imports=["time", "Dict", "Any", "unitree_sdk_interface"],
            supported_robots=[RobotType.G1, RobotType.GO2],
            skill_type=SkillType.BODY_SPECIFIC,
            tags=["movement", "basic", "unitree"],
            examples={
                "move_half_meter": "move_forward(distance=0.5, speed=0.5)",
                "move_far": "move_forward(distance=2.0, speed=0.8)"
            }
        ))
        
        # 2. Rotate
        self.register_template(CodeTemplate(
            template_id="rotate",
            name="Rotate",
            description="Rotate robot by a certain angle",
            category="movement",
            template_code="""# Rotate
import math
from unitree_sdk_interface import MotionController

def rotate(angle: float = 90.0, direction: str = "left", speed: float = 0.5) -> Dict[str, Any]:
    '''
    Rotate robot by angle.
    
    Args:
        angle: Rotation angle in degrees (default: 90.0)
        direction: "left" or "right" (default: "left")
        speed: Rotation speed (0.0-1.0) (default: 0.5)
    
    Returns:
        Dict with success status and execution details
    '''
    try:
        controller = MotionController()
        
        # Convert to radians
        angle_rad = math.radians(angle)
        
        # Direction factor
        dir_factor = -1.0 if direction.lower() == "left" else 1.0
        
        # Execute rotation
        result = controller.rotate(angle_rad * dir_factor, speed)
        
        if result.get("success"):
            return {
                "success": True,
                "angle_rotated": angle,
                "direction": direction,
                "status": "completed"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Rotation failed"),
                "status": "failed"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "error"
        }

# Execute
result = rotate(angle={angle}, direction="{direction}", speed={speed})
return result
""",
            placeholders=["angle", "direction", "speed"],
            required_imports=["math", "Dict", "Any", "unitree_sdk_interface"],
            supported_robots=[RobotType.G1, RobotType.GO2],
            skill_type=SkillType.BODY_SPECIFIC,
            tags=["movement", "rotation", "unitree"]
        ))
        
        # Manipulation templates
        
        # 3. Grasp object
        self.register_template(CodeTemplate(
            template_id="grasp_object",
            name="Grasp Object",
            description="Grasp an object with the robot gripper",
            category="manipulation",
            template_code="""# Grasp object
from unitree_sdk_interface import ManipulationController

def grasp_object(grip_force: float = 50.0, timeout: float = 5.0) -> Dict[str, Any]:
    '''
    Grasp object with gripper.
    
    Args:
        grip_force: Grip force in percentage (0-100) (default: 50.0)
        timeout: Operation timeout in seconds (default: 5.0)
    
    Returns:
        Dict with success status and execution details
    '''
    try:
        controller = ManipulationController()
        
        # Normalize force
        force = max(0, min(100, grip_force))
        
        # Execute grasp
        result = controller.grasp(force, timeout)
        
        if result.get("success"):
            return {
                "success": True,
                "grip_force": force,
                "object_detected": result.get("object_detected", False),
                "status": "grasped"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Grasp failed"),
                "status": "failed"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "error"
        }

# Execute
result = grasp_object(grip_force={grip_force})
return result
""",
            placeholders=["grip_force"],
            required_imports=["Dict", "Any", "unitree_sdk_interface"],
            supported_robots=[RobotType.G1],  # Only G1 has gripper
            skill_type=SkillType.BODY_SPECIFIC,
            tags=["manipulation", "gripper", "grasp"]
        ))
        
        # 4. Release object
        self.register_template(CodeTemplate(
            template_id="release_object",
            name="Release Object",
            description="Release grasped object",
            category="manipulation",
            template_code="""# Release object
from unitree_sdk_interface import ManipulationController

def release_object(timeout: float = 5.0) -> Dict[str, Any]:
    '''
    Release grasped object.
    
    Args:
        timeout: Operation timeout in seconds (default: 5.0)
    
    Returns:
        Dict with success status and execution details
    '''
    try:
        controller = ManipulationController()
        
        # Execute release
        result = controller.release(timeout)
        
        if result.get("success"):
            return {
                "success": True,
                "status": "released"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Release failed"),
                "status": "failed"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "error"
        }

# Execute
result = release_object()
return result
""",
            placeholders=[],
            required_imports=["Dict", "Any", "unitree_sdk_interface"],
            supported_robots=[RobotType.G1],
            skill_type=SkillType.BODY_SPECIFIC,
            tags=["manipulation", "gripper", "release"]
        ))
        
        # Perception templates
        
        # 5. Detect objects
        self.register_template(CodeTemplate(
            template_id="detect_objects",
            name="Detect Objects",
            description="Detect objects in the scene using robot vision",
            category="perception",
            template_code="""# Detect objects
from unitree_sdk_interface import VisionController

def detect_objects(object_type: str = "all", confidence_threshold: float = 0.7) -> Dict[str, Any]:
    '''
    Detect objects in the scene.
    
    Args:
        object_type: Type of object to detect (default: "all")
                    Examples: "all", "person", "ball", "cube"
        confidence_threshold: Detection confidence threshold (default: 0.7)
    
    Returns:
        Dict with detected objects and their properties
    '''
    try:
        controller = VisionController()
        
        # Perform detection
        detections = controller.detect_objects(object_type, confidence_threshold)
        
        if detections:
            return {
                "success": True,
                "objects_detected": len(detections),
                "objects": [
                    {
                        "type": obj.get("type"),
                        "confidence": obj.get("confidence"),
                        "position": obj.get("position"),
                        "size": obj.get("size")
                    }
                    for obj in detections
                ],
                "status": "detected"
            }
        else:
            return {
                "success": True,
                "objects_detected": 0,
                "objects": [],
                "status": "no_objects"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "error"
        }

# Execute
result = detect_objects(object_type="{object_type}", confidence_threshold={confidence_threshold})
return result
""",
            placeholders=["object_type", "confidence_threshold"],
            required_imports=["Dict", "Any", "unitree_sdk_interface"],
            supported_robots=[RobotType.G1, RobotType.GO2],
            skill_type=SkillType.UNIVERSAL,
            tags=["perception", "vision", "detection"]
        ))
        
        logger.info(f"Loaded {len(self.templates)} default code templates")
    
    def register_template(self, template: CodeTemplate) -> None:
        """Register a template in the library.
        
        Args:
            template: CodeTemplate to register
        """
        self.templates[template.template_id] = template
        
        # Index by category
        if template.category not in self.categories:
            self.categories[template.category] = []
        self.categories[template.category].append(template.template_id)
        
        logger.debug(f"Registered template: {template.template_id}")
    
    def get_template(self, template_id: str) -> Optional[CodeTemplate]:
        """Get a template by ID.
        
        Args:
            template_id: Template ID
        
        Returns:
            CodeTemplate or None if not found
        """
        return self.templates.get(template_id)
    
    def list_templates(self, category: Optional[str] = None) -> List[CodeTemplate]:
        """List templates, optionally filtered by category.
        
        Args:
            category: Optional category filter
        
        Returns:
            List of templates
        """
        if category:
            template_ids = self.categories.get(category, [])
            return [self.templates[tid] for tid in template_ids]
        
        return list(self.templates.values())
    
    def get_templates_for_robot(self, robot_type: RobotType) -> List[CodeTemplate]:
        """Get templates compatible with a robot type.
        
        Args:
            robot_type: Target robot type
        
        Returns:
            List of compatible templates
        """
        compatible = []
        for template in self.templates.values():
            if not template.supported_robots or robot_type in template.supported_robots:
                compatible.append(template)
        
        return compatible
    
    def search_templates(self, query: str) -> List[CodeTemplate]:
        """Search templates by name, description, or tags.
        
        Args:
            query: Search query
        
        Returns:
            List of matching templates
        """
        query_lower = query.lower()
        results = []
        
        for template in self.templates.values():
            # Match in name
            if query_lower in template.name.lower():
                results.append(template)
                continue
            
            # Match in description
            if query_lower in template.description.lower():
                results.append(template)
                continue
            
            # Match in tags
            if any(query_lower in tag.lower() for tag in template.tags):
                results.append(template)
                continue
        
        return results
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about templates in the library.
        
        Returns:
            Dict with template statistics
        """
        categories_count = {cat: len(ids) for cat, ids in self.categories.items()}
        robots_count = {}
        for template in self.templates.values():
            for robot in template.supported_robots:
                robots_count[robot.value] = robots_count.get(robot.value, 0) + 1
        
        return {
            "total_templates": len(self.templates),
            "categories": categories_count,
            "robots_supported": robots_count,
            "template_ids": list(self.templates.keys())
        }
