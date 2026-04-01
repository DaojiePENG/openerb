"""Motor Cortex module - Intelligent code generation and execution engine.

This module provides:
- Code template library for common robot skills
- Code generation from intents (template-based and LLM-based)
- Code validation with AST analysis and security checks
- Sandboxed code execution with safety guarantees
- Unitree SDK integration for robot control
"""

from openerb.modules.motor_cortex.motor_cortex import MotorCortex
from openerb.modules.motor_cortex.code_template_library import CodeTemplateLibrary, CodeTemplate
from openerb.modules.motor_cortex.code_generator import CodeGenerator, GeneratedCode
from openerb.modules.motor_cortex.code_validator import CodeValidator, ValidationResult, ValidationIssue
from openerb.modules.motor_cortex.code_executor import CodeExecutor
from openerb.modules.motor_cortex.unitree_sdk_adapter import (
    UnitreeSDKAdapter,
    MotionController,
    ManipulationController,
    VisionController,
    SensorController,
    MotionState
)

__all__ = [
    # Main API
    "MotorCortex",
    
    # Components
    "CodeTemplateLibrary",
    "CodeTemplate",
    "CodeGenerator",
    "GeneratedCode",
    "CodeValidator",
    "ValidationResult",
    "ValidationIssue",
    "CodeExecutor",
    
    # SDK Adapter and Controllers
    "UnitreeSDKAdapter",
    "MotionController",
    "ManipulationController",
    "VisionController",
    "SensorController",
    "MotionState",
]
