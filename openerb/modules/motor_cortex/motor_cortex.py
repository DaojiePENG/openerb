"""Motor Cortex - Main API for intelligent code generation and execution."""

import logging
from typing import Optional, Dict, List, Any
from typing import TYPE_CHECKING
from openerb.core.types import Intent, RobotType, RobotContext, ExecutionResult, CodeExecutionPolicy, Skill, SkillType
from openerb.modules.motor_cortex.code_template_library import CodeTemplateLibrary, CodeTemplate

if TYPE_CHECKING:
    from openerb.llm.base import LLMProvider
from openerb.modules.motor_cortex.code_generator import CodeGenerator, GeneratedCode
from openerb.modules.motor_cortex.code_validator import CodeValidator, ValidationResult
from openerb.modules.motor_cortex.code_executor import CodeExecutor
from openerb.modules.motor_cortex.unitree_sdk_adapter import UnitreeSDKAdapter

logger = logging.getLogger(__name__)


class MotorCortex:
    """Motor Cortex: Intelligent code generation and execution engine.
    
    Coordinates:
    - CodeTemplateLibrary: Predefined skill templates
    - CodeGenerator: Generate code from intents
    - CodeValidator: Validate code safety and syntax
    - CodeExecutor: Execute code in sandbox
    - UnitreeSDKAdapter: Interface to robot hardware
    
    Workflow:
    Intent → Search skill library
           → Generate code (template or LLM)
           → Validate code
           → Execute code
           → Record result
           → Update skill library
    """
    
    def __init__(
        self,
        llm_client: Optional['LLMProvider'] = None,
        robot_type: RobotType = RobotType.G1,
        execution_policy: Optional[CodeExecutionPolicy] = None,
        simulation_mode: bool = True
    ):
        """Initialize Motor Cortex.
        
        Args:
            llm_client: LLM client for code generation
            robot_type: Target robot type
            execution_policy: Security policy for code execution
            simulation_mode: Whether to use simulation mode
        """
        self.robot_type = robot_type
        self.execution_policy = execution_policy or CodeExecutionPolicy()
        self.simulation_mode = simulation_mode
        
        # Initialize components
        self.template_library = CodeTemplateLibrary()
        self.code_generator = CodeGenerator(llm_client, self.template_library)
        self.code_validator = CodeValidator(self.execution_policy)
        self.code_executor = CodeExecutor(self.execution_policy)
        self.sdk_adapter = UnitreeSDKAdapter(robot_type, simulation_mode)
        
        # Execution history
        self.execution_history: Dict[str, Dict] = {}
        self.generated_skills: Dict[str, GeneratedCode] = {}
        
        logger.info(f"Motor Cortex initialized for {robot_type.value} {'(simulation)' if simulation_mode else '(real)'}")
    
    async def process_intent(
        self,
        intent: Intent,
        robot_context: Optional[RobotContext] = None,
        prefer_template: bool = True
    ) -> Dict[str, Any]:
        """Process intent and generate/execute code.
        
        Args:
            intent: User intent to convert to code
            robot_context: Current robot context
            prefer_template: Whether to prefer template generation
        
        Returns:
            Dict with execution results and metadata
        """
        logger.info(f"Processing intent: {intent.action}")
        
        result = {
            "intent": intent,
            "success": False,
            "generated_code": None,
            "validation_result": None,
            "execution_result": None,
            "error": None
        }
        
        try:
            # 1. Generate code (with retry on validation failure)
            max_attempts = 3
            generated = None
            validation = None
            
            for attempt in range(max_attempts):
                if attempt == 0:
                    generated = await self.code_generator.generate_code(
                        intent,
                        robot_context,
                        use_templates=prefer_template
                    )
                else:
                    # Retry with LLM only, adding previous error as feedback
                    logger.info(f"Retry {attempt}/{max_attempts}: regenerating code (previous error: {validation.details})")
                    generated = await self.code_generator.regenerate_without_forbidden(
                        intent, robot_context, validation.details
                    )
                
                if not generated or not generated.code:
                    result["error"] = (generated.error_message if generated else None) or "Code generation failed"
                    return result
                
                result["generated_code"] = generated
                logger.debug(f"Generated code ({generated.complexity}): {len(generated.code)} bytes")
                
                # 2. Validate code
                validation = self.code_validator.validate(generated.code)
                result["validation_result"] = validation
                
                if validation.valid:
                    break
                
                logger.warning(f"Code failed validation (attempt {attempt + 1}): {validation.details}")
                
                # Only retry for forbidden-operation errors (fixable by LLM)
                if "Forbidden" not in (validation.details or ""):
                    result["error"] = validation.details
                    return result
            
            if not validation.valid:
                result["error"] = validation.details
                logger.warning(f"Code failed validation after {max_attempts} attempts: {validation.details}")
                return result
            
            logger.info("Code passed validation")
            
            # 3. Preview execution requirements
            requirements = self.code_executor.estimate_execution_requirements(generated.code)
            result["execution_requirements"] = requirements
            
            # 4. Execute code
            exec_result = self.code_executor.execute(
                generated.code,
                globals_dict={}
            )
            
            result["execution_result"] = exec_result
            result["success"] = exec_result.success
            
            if exec_result.success:
                logger.info(f"Code executed successfully in {exec_result.execution_time:.3f}s")
            else:
                logger.error(f"Code execution failed: {exec_result.error}")
                result["error"] = exec_result.error
            
            # 5. Store execution record
            self._record_execution(intent.action, result)
            
            return result
        
        except Exception as e:
            logger.error(f"Intent processing failed: {e}")
            result["error"] = str(e)
            return result
    
    async def generate_skill(
        self,
        intent: Intent,
        skill_description: Optional[str] = None,
        robot_context: Optional[RobotContext] = None
    ) -> Optional[Skill]:
        """Generate a reusable skill from an intent.
        
        Args:
            intent: Intent to convert to skill
            skill_description: Optional skill description
            robot_context: Robot context
        
        Returns:
            Generated Skill or None
        """
        logger.info(f"Generating skill for: {intent.action}")
        
        # Generate code
        generated = await self.code_generator.generate_code(intent, robot_context)
        
        if not generated.code:
            logger.error(f"Failed to generate code for skill")
            return None
        
        # Validate code
        validation = self.code_validator.validate(generated.code)
        
        if not validation.valid:
            logger.warning(f"Generated code failed validation")
            return None
        
        # Create skill object
        skill = Skill(
            name=intent.action,
            description=skill_description or f"Auto-generated skill for {intent.action}",
            code=generated.code,
            dependencies=["unitree_sdk_interface"],
            tags=["auto_generated", "motor_cortex", generated.complexity],
            supported_robots=[self.robot_type],
            skill_type=SkillType.BODY_SPECIFIC
        )
        
        # Store generated skill
        self.generated_skills[skill.skill_id] = generated
        
        logger.info(f"Generated skill: {skill.skill_id}")
        return skill
    
    def validate_code(self, code: str) -> ValidationResult:
        """Validate code.
        
        Args:
            code: Python code to validate
        
        Returns:
            ValidationResult
        """
        return self.code_validator.validate(code)
    
    def execute_code(
        self,
        code: str,
        globals_dict: Optional[Dict] = None
    ) -> ExecutionResult:
        """Execute code.
        
        Args:
            code: Python code to execute
            globals_dict: Global execution context
        
        Returns:
            ExecutionResult
        """
        return self.code_executor.execute(code, globals_dict)
    
    def execute_skill(
        self,
        skill: Skill,
        parameters: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """Execute a skill.
        
        Args:
            skill: Skill to execute
            parameters: Parameters for skill execution
        
        Returns:
            ExecutionResult
        """
        logger.info(f"Executing skill: {skill.name}")
        
        # Get robot-specific variant if available
        code = skill.adaptations.get(self.robot_type, skill.code)
        
        # Build execution context
        globals_dict = {
            "skill_name": skill.name,
            "skill_id": skill.skill_id,
            "parameters": parameters or {}
        }
        
        # Execute
        result = self.code_executor.execute(code, globals_dict)
        
        # Record execution
        self._record_execution(skill.name, {
            "skill_id": skill.skill_id,
            "execution_result": result
        })
        
        return result
    
    def get_template(self, template_id: str) -> Optional[CodeTemplate]:
        """Get a template by ID.
        
        Args:
            template_id: Template ID
        
        Returns:
            CodeTemplate or None
        """
        return self.template_library.get_template(template_id)
    
    def list_templates(
        self,
        category: Optional[str] = None,
        robot_type: Optional[RobotType] = None
    ) -> List[CodeTemplate]:
        """List available templates.
        
        Args:
            category: Optional category filter
            robot_type: Optional robot type filter
        
        Returns:
            List of templates
        """
        templates = self.template_library.list_templates(category)
        
        if robot_type:
            templates = [
                t for t in templates
                if not t.supported_robots or robot_type in t.supported_robots
            ]
        
        return templates
    
    def search_templates(self, query: str) -> List[CodeTemplate]:
        """Search templates.
        
        Args:
            query: Search query
        
        Returns:
            List of matching templates
        """
        return self.template_library.search_templates(query)
    
    def _record_execution(self, action: str, result: Dict) -> None:
        """Record execution in history.
        
        Args:
            action: Action name
            result: Execution result
        """
        import time
        record_id = f"{action}_{time.time()}"
        self.execution_history[record_id] = {
            "action": action,
            "timestamp": time.time(),
            "result": result
        }
    
    def get_execution_history(self, action: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Get execution history.
        
        Args:
            action: Optional action filter
            limit: Maximum records to return
        
        Returns:
            List of execution records
        """
        records = list(self.execution_history.values())
        
        if action:
            records = [r for r in records if r["action"] == action]
        
        # Sort by timestamp descending
        records.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return records[:limit]
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get Motor Cortex system statistics.
        
        Returns:
            Dict with system statistics
        """
        return {
            "robot_type": self.robot_type.value,
            "simulation_mode": self.simulation_mode,
            "templates": {
                "total": len(self.template_library.templates),
                "stats": self.template_library.get_template_stats()
            },
            "code_generation": self.code_generator.get_generation_stats(),
            "executions": {
                "total": len(self.execution_history),
                "recent_10": len(self.get_execution_history(limit=10))
            },
            "generated_skills": len(self.generated_skills),
            "sdk_adapter": self.sdk_adapter.get_adapter_stats()
        }
    
    async def update_execution_policy(self, policy: CodeExecutionPolicy) -> None:
        """Update code execution policy.
        
        Args:
            policy: New CodeExecutionPolicy
        """
        self.execution_policy = policy
        self.code_validator = CodeValidator(policy)
        self.code_executor = CodeExecutor(policy)
        logger.info("Execution policy updated")
    
    def preview_code_execution(self, code: str) -> Dict[str, Any]:
        """Preview code execution without running it.
        
        Args:
            code: Code to preview
        
        Returns:
            Preview information
        """
        return self.code_executor.preview_execution(code)
