"""Unitree SDK Adapter - Unified interface to Unitree robot SDK."""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from openerb.core.types import RobotType, ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class MotionState:
    """Current motion state of the robot."""
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # x, y, z
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    yaw: float = 0.0  # Rotation angle
    is_moving: bool = False


@dataclass
class DetectionResult:
    """Result from vision/sensor detection."""
    object_type: str
    confidence: float
    position: Tuple[float, float, float]
    size: Optional[Tuple[float, float, float]] = None
    properties: Dict[str, Any] = field(default_factory=dict)


class MotionController:
    """Control robot motion/locomotion."""
    
    def __init__(self):
        """Initialize motion controller."""
        self.state = MotionState()
        self._simulation_mode = True
        logger.info("MotionController initialized (simulation mode)")
    
    def move_forward(self, velocity: float = 0.5, duration: float = 1.0) -> Dict[str, Any]:
        """Move robot forward.
        
        Args:
            velocity: Forward velocity (m/s, range: 0.0-1.0)
            duration: Duration of movement (seconds)
        
        Returns:
            Dict with execution result
        """
        try:
            if not 0.0 <= velocity <= 1.0:
                return {"success": False, "error": "Velocity out of range [0.0-1.0]"}
            
            if self._simulation_mode:
                # Simulate movement
                distance = velocity * duration
                self.state.position = (
                    self.state.position[0] + distance,
                    self.state.position[1],
                    self.state.position[2]
                )
                self.state.velocity = (velocity, 0.0, 0.0)
                
                logger.info(f"Forward motion: {distance}m at {velocity}m/s")
                return {
                    "success": True,
                    "distance_moved": distance,
                    "time_taken": duration
                }
            else:
                # Real SDK call would go here
                return {"success": True, "distance_moved": velocity * duration}
        
        except Exception as e:
            logger.error(f"Motion failed: {e}")
            return {"success": False, "error": str(e)}
    
    def move_backward(self, velocity: float = 0.5, duration: float = 1.0) -> Dict[str, Any]:
        """Move robot backward."""
        return self.move_forward(-velocity, duration)
    
    def rotate(self, angle_rad: float = 1.57, speed: float = 0.5) -> Dict[str, Any]:
        """Rotate robot.
        
        Args:
            angle_rad: Rotation angle in radians (positive = counter-clockwise)
            speed: Rotation speed (0.0-1.0)
        
        Returns:
            Dict with execution result
        """
        try:
            if self._simulation_mode:
                self.state.yaw += angle_rad
                logger.info(f"Rotation: {angle_rad} rad at {speed} speed")
                return {
                    "success": True,
                    "angle_rotated": angle_rad,
                    "speed": speed
                }
            else:
                return {"success": True}
        
        except Exception as e:
            logger.error(f"Rotation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def stand_up(self) -> Dict[str, Any]:
        """Make robot stand up."""
        try:
            logger.info("Standing up")
            return {"success": True, "status": "standing"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def sit_down(self) -> Dict[str, Any]:
        """Make robot sit down."""
        try:
            logger.info("Sitting down")
            return {"success": True, "status": "sitting"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_state(self) -> MotionState:
        """Get current motion state."""
        return self.state


class ManipulationController:
    """Control robot manipulation (gripper, arms, etc.)."""
    
    def __init__(self):
        """Initialize manipulation controller."""
        self.gripper_open = True
        self.grip_force = 0.0
        self._simulation_mode = True
        logger.info("ManipulationController initialized (simulation mode)")
    
    def grasp(self, force: float = 50.0, timeout: float = 5.0) -> Dict[str, Any]:
        """Grasp object.
        
        Args:
            force: Grip force in percentage (0-100)
            timeout: Operation timeout (seconds)
        
        Returns:
            Dict with execution result
        """
        try:
            if not 0.0 <= force <= 100.0:
                return {"success": False, "error": "Force out of range [0-100]"}
            
            self.gripper_open = False
            self.grip_force = force
            
            logger.info(f"Grasping with force {force}%")
            return {
                "success": True,
                "grip_force": force,
                "object_detected": True
            }
        
        except Exception as e:
            logger.error(f"Grasp failed: {e}")
            return {"success": False, "error": str(e)}
    
    def release(self, timeout: float = 5.0) -> Dict[str, Any]:
        """Release grasped object."""
        try:
            self.gripper_open = True
            self.grip_force = 0.0
            
            logger.info("Released object")
            return {"success": True, "status": "released"}
        
        except Exception as e:
            logger.error(f"Release failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_gripper_state(self) -> Dict[str, Any]:
        """Get gripper state."""
        return {
            "open": self.gripper_open,
            "force": self.grip_force
        }


class VisionController:
    """Control robot vision and perception."""
    
    def __init__(self):
        """Initialize vision controller."""
        self._simulation_mode = True
        logger.info("VisionController initialized (simulation mode)")
    
    def detect_objects(
        self, 
        object_type: str = "all",
        confidence_threshold: float = 0.7
    ) -> List[DetectionResult]:
        """Detect objects in scene.
        
        Args:
            object_type: Type of object to detect
            confidence_threshold: Minimum confidence for detection
        
        Returns:
            List of detected objects
        """
        try:
            if self._simulation_mode:
                # Simulate detection
                if object_type == "all":
                    return [
                        DetectionResult(
                            object_type="cube",
                            confidence=0.95,
                            position=(1.0, 0.0, 0.5),
                            size=(0.1, 0.1, 0.1)
                        ),
                        DetectionResult(
                            object_type="ball",
                            confidence=0.87,
                            position=(0.5, 0.5, 0.3),
                            size=(0.08, 0.08, 0.08)
                        )
                    ]
                else:
                    return [
                        DetectionResult(
                            object_type=object_type,
                            confidence=0.9,
                            position=(1.0, 0.0, 0.5)
                        )
                    ]
            
            return []
        
        except Exception as e:
            logger.error(f"Detection failed: {e}")
            return []
    
    def detect_person(self, confidence_threshold: float = 0.8) -> List[Dict]:
        """Detect person(s) in scene."""
        results = self.detect_objects("person", confidence_threshold)
        return [
            {
                "person_id": i,
                "confidence": r.confidence,
                "position": r.position
            }
            for i, r in enumerate(results)
        ]
    
    def track_object(self, object_id: str) -> Optional[Dict]:
        """Track a specific object."""
        return {
            "object_id": object_id,
            "position": (1.0, 0.0, 0.5),
            "velocity": (0.1, 0.0, 0.0)
        }


class SensorController:
    """Access robot sensors (IMU, battery, etc.)."""
    
    def __init__(self):
        """Initialize sensor controller."""
        self._simulation_mode = True
        logger.info("SensorController initialized (simulation mode)")
    
    def get_battery_level(self) -> float:
        """Get battery level percentage."""
        return 85.0  # Simulated
    
    def get_imu_data(self) -> Dict[str, Any]:
        """Get IMU (accelerometer, gyroscope) data."""
        return {
            "acceleration": (0.0, 0.0, 9.8),
            "angular_velocity": (0.0, 0.0, 0.0),
            "temperature": 35.0
        }
    
    def get_foot_force(self) -> Dict[str, List[float]]:
        """Get foot force readings."""
        return {
            "front_left": [50.0, 50.0, 50.0],
            "front_right": [50.0, 50.0, 50.0],
            "rear_left": [50.0, 50.0, 50.0],
            "rear_right": [50.0, 50.0, 50.0]
        }


class UnitreeSDKAdapter:
    """Unified adapter for Unitree SDK."""
    
    def __init__(self, robot_type: RobotType = RobotType.G1, simulation: bool = True):
        """Initialize SDK adapter.
        
        Args:
            robot_type: Target robot type
            simulation: Whether to use simulation mode
        """
        self.robot_type = robot_type
        self.motion = MotionController()
        self.manipulation = ManipulationController()
        self.vision = VisionController()
        self.sensor = SensorController()
        
        # Set simulation mode for all controllers
        self.motion._simulation_mode = simulation
        self.manipulation._simulation_mode = simulation
        self.vision._simulation_mode = simulation
        self.sensor._simulation_mode = simulation
        
        logger.info(f"Unitree SDK Adapter initialized for {robot_type.value} in {'simulation' if simulation else 'real'} mode")
    
    def execute_skill_code(self, code: str, globals_dict: Optional[Dict] = None) -> ExecutionResult:
        """Execute skill code in adapter context.
        
        Args:
            code: Python code to execute
            globals_dict: Global environment variables
        
        Returns:
            ExecutionResult with execution details
        """
        if globals_dict is None:
            globals_dict = {}
        
        # Add controllers to execution environment
        globals_dict.update({
            "MotionController": MotionController,
            "ManipulationController": ManipulationController,
            "VisionController": VisionController,
            "SensorController": SensorController,
            "Dict": Dict,
            "Any": Any,
        })
        
        try:
            local_vars = {}
            exec(code, globals_dict, local_vars)
            
            result = local_vars.get("result")
            return ExecutionResult(
                success=True,
                output=str(result),
                execution_time=0.0
            )
        
        except Exception as e:
            logger.error(f"Skill execution failed: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=str(e)
            )
    
    def get_adapter_stats(self) -> Dict[str, Any]:
        """Get adapter statistics."""
        return {
            "robot_type": self.robot_type.value,
            "motion_state": {
                "position": self.motion.state.position,
                "yaw": self.motion.state.yaw,
                "velocity": self.motion.state.velocity
            },
            "gripper_state": self.manipulation.get_gripper_state(),
            "battery": self.sensor.get_battery_level()
        }
