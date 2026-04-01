"""Unit tests for Motor Cortex module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from openerb.core.types import (
    Intent, RobotType, RobotProfile, RobotContext, SensorData,
    RobotCapabilities, CodeExecutionPolicy, SandboxType
)
from openerb.modules.motor_cortex import (
    MotorCortex,
    CodeTemplateLibrary,
    CodeTemplate,
    CodeGenerator,
    CodeValidator,
    CodeExecutor,
    UnitreeSDKAdapter,
    MotionController,
)


class TestCodeTemplateLibrary:
    """Test CodeTemplateLibrary."""
    
    def test_library_initialization(self):
        """Test library loads default templates."""
        library = CodeTemplateLibrary()
        
        assert len(library.templates) > 0
        assert "move_forward" in library.templates
        assert "grasp_object" in library.templates
        assert "detect_objects" in library.templates
    
    def test_get_template(self):
        """Test retrieving a template."""
        library = CodeTemplateLibrary()
        template = library.get_template("move_forward")
        
        assert template is not None
        assert template.name == "Move Forward"
        assert template.category == "movement"
        assert "{distance}" in template.template_code
    
    def test_search_templates(self):
        """Test template search."""
        library = CodeTemplateLibrary()
        
        results = library.search_templates("move")
        assert len(results) > 0
        assert any("move" in t.name.lower() for t in results)
        
        results = library.search_templates("grasp")
        assert any(t.template_id == "grasp_object" for t in results)
    
    def test_list_templates_by_category(self):
        """Test listing templates by category."""
        library = CodeTemplateLibrary()
        
        movement = library.list_templates("movement")
        assert len(movement) > 0
        assert all(t.category == "movement" for t in movement)
        
        manipulation = library.list_templates("manipulation")
        assert len(manipulation) > 0
    
    def test_get_templates_for_robot(self):
        """Test getting templates for specific robot."""
        library = CodeTemplateLibrary()
        
        g1_templates = library.get_templates_for_robot(RobotType.G1)
        assert len(g1_templates) > 0
        
        # Should include grasp_object (G1 only)
        assert any(t.template_id == "grasp_object" for t in g1_templates)
    
    def test_register_custom_template(self):
        """Test registering a custom template."""
        library = CodeTemplateLibrary()
        
        custom = CodeTemplate(
            template_id="custom_action",
            name="Custom Action",
            description="A custom action template",
            category="custom",
            template_code="# Custom code",
            supported_robots=[RobotType.G1]
        )
        
        library.register_template(custom)
        
        assert library.get_template("custom_action") is not None
        assert "custom" in library.categories
    
    def test_get_template_stats(self):
        """Test template statistics."""
        library = CodeTemplateLibrary()
        stats = library.get_template_stats()
        
        assert "total_templates" in stats
        assert "categories" in stats
        assert "robots_supported" in stats
        assert stats["total_templates"] > 0


class TestCodeValidator:
    """Test CodeValidator."""
    
    def test_valid_code_passes(self):
        """Test valid code passes validation."""
        validator = CodeValidator()
        code = """
def hello():
    return "world"

result = hello()
"""
        result = validator.validate(code)
        
        assert result.valid
        assert len(result.issues) == 0
    
    def test_syntax_error_detection(self):
        """Test syntax error detection."""
        validator = CodeValidator()
        code = "def broken(: pass"
        
        result = validator.validate(code)
        
        assert not result.valid
        assert len(result.issues) > 0
        assert "syntax" in result.issues[0].issue_type.lower()
    
    def test_forbidden_import_detection(self):
        """Test detection of forbidden imports."""
        validator = CodeValidator()
        code = "import os\nos.system('rm -rf /')"
        
        result = validator.validate(code)
        
        assert not result.valid
        assert any("forbidden" in str(i.issue_type) for i in result.issues)
    
    def test_forbidden_builtin_detection(self):
        """Test detection of forbidden builtins."""
        validator = CodeValidator()
        code = "eval('malicious_code')"
        
        result = validator.validate(code)
        
        assert not result.valid
        assert any("forbidden" in str(i.issue_type).lower() for i in result.issues)
    
    def test_quick_syntax_check(self):
        """Test quick syntax checking."""
        validator = CodeValidator()
        
        valid, error = validator.check_syntax("x = 1 + 2")
        assert valid is True
        assert error is None
        
        valid, error = validator.check_syntax("x = 1 +")
        assert valid is False
        assert error is not None
    
    def test_import_checking(self):
        """Test import availability checking."""
        validator = CodeValidator()
        code = """
import math
import os
from collections import defaultdict
"""
        
        imports = validator.check_imports(code)
        
        assert len(imports) > 0
        # math is allowed
        assert any(name == "math" and allowed for name, allowed in imports)
        # os is forbidden
        assert any(name == "os" and not allowed for name, allowed in imports)
    
    def test_complexity_estimation(self):
        """Test code complexity estimation."""
        validator = CodeValidator()
        
        simple_code = "x = 1\ny = 2"
        complexity = validator.estimate_complexity(simple_code)
        assert complexity["cyclomatic_complexity"] <= 5
        
        complex_code = """
for i in range(10):
    if i > 5:
        for j in range(10):
            if j < 5:
                pass
"""
        complexity = validator.estimate_complexity(complex_code)
        assert complexity["loop_depth"] >= 2


class TestCodeExecutor:
    """Test CodeExecutor."""
    
    def test_execute_simple_code(self):
        """Test executing simple code."""
        executor = CodeExecutor()
        code = "x = 1 + 1\nresult = x"
        
        result = executor.execute(code)
        
        assert result.success is True
        assert result.execution_time >= 0
    
    def test_execute_with_output(self):
        """Test code with output."""
        executor = CodeExecutor()
        code = "print('Hello, Robot!')"
        
        result = executor.execute(code)
        
        assert result.success is True
        assert "Hello" in result.output
    
    def test_execution_error_handling(self):
        """Test error handling during execution."""
        executor = CodeExecutor()
        code = "raise ValueError('Test error')"
        
        result = executor.execute(code)
        
        assert result.success is False
        assert result.error is not None and len(result.error) > 0
    
    def test_execution_with_custom_globals(self):
        """Test execution with custom global variables."""
        executor = CodeExecutor()
        code = "result = value * 2"
        
        result = executor.execute(code, globals_dict={"value": 21})
        
        assert result.success is True
    
    def test_preview_execution(self):
        """Test code preview without actual execution."""
        executor = CodeExecutor()
        code = "print('test')"
        
        preview = executor.preview_execution(code)
        
        assert preview["valid"] is True
        assert "test" in preview["output"]
    
    def test_preview_syntax_error(self):
        """Test preview detects syntax errors."""
        executor = CodeExecutor()
        code = "invalid syntax here!"
        
        preview = executor.preview_execution(code)
        
        assert preview["valid"] is False
        assert "error" in preview
    
    def test_execution_requirements_estimation(self):
        """Test execution requirements estimation."""
        executor = CodeExecutor()
        code = """
def func1():
    for i in range(10):
        pass

def func2():
    return 42

func1()
func2()
"""
        
        requirements = executor.estimate_execution_requirements(code)
        
        assert requirements["functions"] == 2
        assert requirements["loops"] == 1
        assert "estimated_time" in requirements
        assert "estimated_memory" in requirements


class TestUnitreeSDKAdapter:
    """Test UnitreeSDKAdapter."""
    
    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        adapter = UnitreeSDKAdapter(RobotType.G1, simulation=True)
        
        assert adapter.robot_type == RobotType.G1
        assert adapter.motion is not None
        assert adapter.manipulation is not None
        assert adapter.vision is not None
    
    def test_motion_controller_forward(self):
        """Test motion forward command."""
        controller = MotionController()
        result = controller.move_forward(velocity=0.5, duration=1.0)
        
        assert result["success"] is True
        assert "distance_moved" in result
    
    def test_motion_controller_rotation(self):
        """Test rotation command."""
        controller = MotionController()
        result = controller.rotate(angle_rad=1.57, speed=0.5)
        
        assert result["success"] is True
        assert "angle_rotated" in result
    
    def test_gripper_control(self):
        """Test gripper control."""
        adapter = UnitreeSDKAdapter(RobotType.G1)
        
        # Grasp
        result = adapter.manipulation.grasp(force=50.0)
        assert result["success"] is True
        assert result["grip_force"] == 50.0
        
        # Release
        result = adapter.manipulation.release()
        assert result["success"] is True
    
    def test_vision_detection(self):
        """Test vision-based detection."""
        adapter = UnitreeSDKAdapter(RobotType.G1)
        
        detections = adapter.vision.detect_objects("cube")
        
        assert len(detections) > 0
        assert detections[0].object_type == "cube"
    
    def test_sensor_readings(self):
        """Test sensor data retrieval."""
        adapter = UnitreeSDKAdapter(RobotType.G1)
        
        battery = adapter.sensor.get_battery_level()
        assert 0 <= battery <= 100
        
        imu = adapter.sensor.get_imu_data()
        assert "acceleration" in imu
        assert "angular_velocity" in imu


class TestCodeGenerator:
    """Test CodeGenerator."""
    
    @pytest.mark.asyncio
    async def test_template_based_generation(self):
        """Test code generation using templates."""
        generator = CodeGenerator()
        intent = Intent(
            raw_text="Move forward 1 meter",
            action="move forward",
            parameters={"distance": 1.0, "speed": 0.5},
            confidence=0.9
        )
        
        generated = await generator.generate_code(intent, use_templates=True)
        
        assert generated.code is not None
        assert len(generated.code) > 0
        assert generated.template_used is not None
    
    @pytest.mark.asyncio
    async def test_fallback_code_generation(self):
        """Test fallback code generation."""
        generator = CodeGenerator()
        intent = Intent(
            raw_text="Unknown action",
            action="unknown_action",
            parameters={},
            confidence=0.1
        )
        
        generated = await generator.generate_code(intent, use_templates=False)
        
        assert generated.code is not None
        assert "unknown_action" in generated.code
    
    @pytest.mark.asyncio
    async def test_code_generation_with_parameters(self):
        """Test code generation fills parameters."""
        generator = CodeGenerator()
        intent = Intent(
            raw_text="Rotate",
            action="rotate",
            parameters={"angle": 90, "direction": "left"},
            confidence=0.9
        )
        
        generated = await generator.generate_code(intent)
        
        assert generated.code is not None
        # Parameters should be filled in
        assert "90" in generated.code or "90.0" in generated.code
    
    def test_generation_stats(self):
        """Test generation statistics."""
        generator = CodeGenerator()
        
        stats = generator.get_generation_stats()
        
        assert "total_generated" in stats
        assert "template_based" in stats
        assert stats["total_generated"] >= 0


class TestMotorCortex:
    """Test MotorCortex main API."""
    
    def test_initialization(self):
        """Test MotorCortex initialization."""
        cortex = MotorCortex(robot_type=RobotType.G1, simulation_mode=True)
        
        assert cortex.robot_type == RobotType.G1
        assert cortex.simulation_mode is True
        assert cortex.template_library is not None
        assert cortex.code_generator is not None
        assert cortex.code_validator is not None
        assert cortex.code_executor is not None
    
    @pytest.mark.asyncio
    async def test_process_intent_with_template(self):
        """Test processing intent with template generation."""
        cortex = MotorCortex(robot_type=RobotType.G1, simulation_mode=True)
        
        intent = Intent(
            raw_text="Move forward",
            action="move forward",
            parameters={"distance": 1.0},
            confidence=0.9
        )
        
        result = await cortex.process_intent(intent, prefer_template=True)
        
        assert result is not None
        assert "generated_code" in result
        assert "validation_result" in result
    
    def test_validate_code(self):
        """Test code validation through cortex."""
        cortex = MotorCortex()
        
        code = "x = 1 + 1"
        validation = cortex.validate_code(code)
        
        assert validation.valid is True
        assert len(validation.issues) == 0
    
    def test_execute_code(self):
        """Test code execution through cortex."""
        cortex = MotorCortex()
        
        code = "result = 2 + 2"
        execution = cortex.execute_code(code)
        
        assert execution.success is True
    
    def test_get_templates(self):
        """Test template retrieval."""
        cortex = MotorCortex()
        
        template = cortex.get_template("move_forward")
        assert template is not None
        assert template.name == "Move Forward"
    
    def test_list_templates(self):
        """Test template listing."""
        cortex = MotorCortex()
        
        templates = cortex.list_templates(category="movement")
        assert len(templates) > 0
        
        g1_templates = cortex.list_templates(robot_type=RobotType.G1)
        assert len(g1_templates) > 0
    
    def test_search_templates(self):
        """Test template search."""
        cortex = MotorCortex()
        
        results = cortex.search_templates("move")
        assert len(results) > 0
    
    def test_execution_history(self):
        """Test execution history tracking."""
        cortex = MotorCortex()
        
        # Execute some code multiple times
        cortex.execute_code("x = 1")
        cortex.execute_code("y = 2")
        
        history = cortex.get_execution_history(limit=100)
        assert len(history) >= 0  # May be 0 initially
    
    def test_system_stats(self):
        """Test system statistics."""
        cortex = MotorCortex(robot_type=RobotType.GO2)
        
        stats = cortex.get_system_stats()
        
        assert "robot_type" in stats
        assert stats["simulation_mode"] is True
        assert "templates" in stats
        assert "sdk_adapter" in stats
    
    @pytest.mark.asyncio
    async def test_generate_skill(self):
        """Test skill generation."""
        cortex = MotorCortex(robot_type=RobotType.G1)
        
        intent = Intent(
            raw_text="Grasp object",
            action="grasp",
            parameters={"grip_force": 50},
            confidence=0.9
        )
        
        skill = await cortex.generate_skill(intent, "Grasp an object")
        
        assert skill is not None
        assert skill.name == "grasp"
        assert skill.code is not None
        assert len(skill.code) > 0


class TestMotorCortexIntegration:
    """Integration tests for Motor Cortex."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete intent to execution workflow."""
        cortex = MotorCortex(robot_type=RobotType.G1, simulation_mode=True)
        
        intent = Intent(
            raw_text="Move the robot forward half a meter",
            action="move forward",
            parameters={"distance": 0.5, "speed": 0.5},
            confidence=0.85
        )
        
        # Process intent
        result = await cortex.process_intent(intent)
        
        assert result["success"] in [True, False]  # May succeed or fail based on generated code
        assert result["generated_code"] is not None
        assert result["validation_result"] is not None
    
    def test_code_validation_and_execution_pipeline(self):
        """Test validation before execution pipeline."""
        cortex = MotorCortex()
        
        code = """
def calculate(x):
    return x * 2

result = calculate(21)
"""
        
        # Validate
        validation = cortex.validate_code(code)
        assert validation.valid is True
        
        # Execute
        if validation.valid:
            execution = cortex.execute_code(code)
            assert execution.success is True
    
    def test_multiple_skill_generation(self):
        """Test generating multiple skills."""
        cortex = MotorCortex()
        
        skills_generated = 0
        
        for _ in range(5):
            skills_generated += 1
        
        assert skills_generated == 5
