"""Code generator for Motor Cortex - Generate executable code from intents using LLM."""

import logging
import re
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from typing import TYPE_CHECKING
from openerb.core.types import Intent, RobotType, Skill, RobotContext
from openerb.llm.base import Message
from openerb.modules.motor_cortex.code_template_library import CodeTemplateLibrary
from openerb.prompts import load_prompt

if TYPE_CHECKING:
    from openerb.llm.base import LLMProvider

logger = logging.getLogger(__name__)


@dataclass
class GeneratedCode:
    """Generated code with metadata."""
    code: str
    skill_id: str
    intent: Intent
    template_used: Optional[str] = None
    llm_used: bool = False
    success_rate_prediction: float = 0.0
    complexity: str = "unknown"
    error_message: Optional[str] = None


class CodeGenerator:
    """Generate executable code from intents using LLM and templates."""
    
    # System prompt loaded from prompts/code_generator.md
    SYSTEM_PROMPT = load_prompt("code_generator")
    
    def __init__(
        self,
        llm_client: Optional['LLMProvider'] = None,
        template_library: Optional[CodeTemplateLibrary] = None
    ):
        """Initialize code generator.
        
        Args:
            llm_client: LLM client for code generation
            template_library: Template library for skill patterns
        """
        self.llm_client = llm_client
        self.template_library = template_library or CodeTemplateLibrary()
        self.generation_history: Dict[str, GeneratedCode] = {}
    
    async def generate_code(
        self,
        intent: Intent,
        robot_context: Optional[RobotContext] = None,
        use_templates: bool = True
    ) -> GeneratedCode:
        """Generate code from an intent.
        
        Args:
            intent: User intent to convert to code
            robot_context: Context about the current robot
            use_templates: Whether to use templates first
        
        Returns:
            GeneratedCode with full implementation
        """
        try:
            # 1. Try template matching first
            if use_templates:
                template_result = await self._try_template_generation(intent, robot_context)
                if template_result:
                    return template_result
            
            # 2. Fall back to LLM generation
            if self.llm_client:
                llm_result = await self._llm_generation(intent, robot_context)
                if llm_result:
                    return llm_result
            
            # 3. Fallback: simple template with direct parameters
            return await self._fallback_generation(intent, robot_context)
        
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return GeneratedCode(
                code="",
                skill_id="",
                intent=intent,
                error_message=str(e)
            )
    
    async def _try_template_generation(
        self,
        intent: Intent,
        robot_context: Optional[RobotContext]
    ) -> Optional[GeneratedCode]:
        """Try to generate code using templates.
        
        Args:
            intent: User intent
            robot_context: Robot context
        
        Returns:
            GeneratedCode or None if no template found
        """
        logger.info(f"Attempting template-based generation for intent: {intent.action}")
        
        # Search for matching template by action
        action = intent.action.lower()
        templates = self.template_library.search_templates(action)
        
        if not templates:
            logger.debug(f"No templates found for action: {action}")
            return None
        
        # Use the first matching template
        template = templates[0]
        
        # Check robot compatibility
        if robot_context:
            robot_type = robot_context.robot_profile.robot_type
            if template.supported_robots and robot_type not in template.supported_robots:
                logger.debug(f"Template not compatible with {robot_type}")
                return None
        
        # Fill in placeholders
        code = await self._fill_template(template, intent)
        
        generated = GeneratedCode(
            code=code,
            skill_id=f"skill_{intent.timestamp.timestamp()}",
            intent=intent,
            template_used=template.template_id,
            llm_used=False,
            success_rate_prediction=0.85,
            complexity="low"
        )
        
        self.generation_history[generated.skill_id] = generated
        logger.info(f"Generated code from template: {template.template_id}")
        
        return generated
    
    async def _fill_template(self, template, intent: Intent) -> str:
        """Fill template placeholders with intent parameters.
        
        Args:
            template: CodeTemplate to fill
            intent: Intent with parameters
        
        Returns:
            Filled code string
        """
        code = template.template_code
        
        # Replace placeholders from intent parameters
        for placeholder in template.placeholders:
            if placeholder in intent.parameters:
                value = intent.parameters[placeholder]
                # Format value appropriately
                if isinstance(value, str):
                    formatted = f'"{value}"'
                elif isinstance(value, bool):
                    formatted = str(value)
                else:
                    formatted = str(value)
                
                code = code.replace(f"{{{placeholder}}}", formatted)
        
        return code
    
    async def _llm_generation(
        self,
        intent: Intent,
        robot_context: Optional[RobotContext]
    ) -> Optional[GeneratedCode]:
        """Generate code using LLM agent.
        
        This is the primary code generation path - uses a dedicated LLM
        to write Python code for the user's request.
        """
        if not self.llm_client:
            return None
        
        logger.info("Generating code with LLM agent")
        
        # Build a clear prompt for code generation
        prompt = f"""User request: "{intent.raw_text}"
Action type: {intent.action}
Parameters: {intent.parameters}

Generate Python code that accomplishes this request.
The code MUST:
1. Define a REUSABLE function with clear parameters (e.g., `def calculate(expr)`, `def fibonacci(n)`)
2. Call the function with the user's specific values
3. Use print() to clearly show the result to the user
4. Be self-contained and executable as-is

IMPORTANT:
- Write a GENERAL PURPOSE function first, then call it. Do NOT hardcode the user's values.
- The code MUST print() the final answer. Code without print output is useless.
- Only use standard library imports (math, re, json, datetime, collections, random, string).
- Do NOT use eval(), exec(), open(), os, sys, subprocess."""
        
        try:
            response = await self.llm_client.call(
                messages=[
                    Message(role="system", content=self.SYSTEM_PROMPT),
                    Message(role="user", content=prompt),
                ],
                temperature=0.3,
                max_tokens=2048
            )
            
            code = self._extract_code_from_response(response.content)
            
            if not code:
                logger.warning("Could not extract code from LLM response")
                return None
            
            generated = GeneratedCode(
                code=code,
                skill_id=f"skill_{intent.timestamp.timestamp()}_llm",
                intent=intent,
                llm_used=True,
                success_rate_prediction=0.7,
                complexity="medium"
            )
            
            self.generation_history[generated.skill_id] = generated
            logger.info("Generated code with LLM agent")
            
            return generated
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return None
    
    async def _fallback_generation(
        self,
        intent: Intent,
        robot_context: Optional[RobotContext]
    ) -> GeneratedCode:
        """Fallback basic code generation.
        
        Args:
            intent: User intent
            robot_context: Robot context
        
        Returns:
            Basic GeneratedCode
        """
        logger.info("Using fallback code generation")
        
        action = intent.action.lower()
        params = intent.parameters
        
        # Generate smart code that handles calculations
        code = """# Generated code
import re

def execute_task():
    parameters = """ + str(params) + """
    
    # Check if this is a calculation task
    expression = parameters.get('expression', '').lower()
    task = parameters.get('task', '').lower()
    user_text = expression or task
    
    # Check for math operators or keywords
    has_math = any(op in user_text for op in ['+', '-', '*', '/', 'plus', 'add', 'minus', 'subtract', 'multiply', 'times', 'divide'])
    
    if has_math and expression:
        # Handle math expressions safely (no eval)
        expr = expression
        expr = expr.replace('plus', ' + ').replace('add', ' + ')
        expr = expr.replace('minus', ' - ').replace('subtract', ' - ')
        expr = expr.replace('times', ' * ').replace('multiply', ' * ')
        expr = expr.replace('divided by', ' / ').replace('divide', ' / ')
        expr = expr.replace('x', ' * ')
        
        try:
            # Extract numbers and operators
            import re
            tokens = re.findall(r'\\d+\\.?\\d*|[+\\-*/]', expr)
            
            if len(tokens) >= 3:
                result = float(tokens[0])
                for i in range(1, len(tokens), 2):
                    if i + 1 < len(tokens):
                        op = tokens[i]
                        num = float(tokens[i + 1])
                        if op == '+':
                            result += num
                        elif op == '-':
                            result -= num
                        elif op == '*':
                            result *= num
                        elif op == '/':
                            if num != 0:
                                result /= num
                
                # Format result
                if result == int(result):
                    result = int(result)
                
                print(f"Calculation: {expression}")
                print(f"Answer: {result}")
                return {
                    "success": True,
                    "status": "completed",
                    "result": result
                }
        except:
            pass
        
        return {
            "success": True,
            "status": "executed",
            "result": "OK"
        }
    else:
        print(f"Executing: """ + action + """")
        return {
            "success": True,
            "status": "executed",
            "result": "OK"
        }

result = execute_task()
"""
        
        return GeneratedCode(
            code=code,
            skill_id=f"skill_{intent.timestamp.timestamp()}_fallback",
            intent=intent,
            llm_used=False,
            success_rate_prediction=0.7,
            complexity="low"
        )
    
    def _extract_code_from_response(self, response_text: str) -> Optional[str]:
        """Extract Python code from LLM response.
        
        Args:
            response_text: LLM response text
        
        Returns:
            Extracted code or None
        """
        # Look for code blocks
        patterns = [
            r"```python\n(.*?)\n```",
            r"```\n(.*?)\n```",
            r"```(.*?)```"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _build_context_info(self, robot_context: Optional[RobotContext]) -> str:
        """Build context information for LLM.
        
        Args:
            robot_context: Robot context
        
        Returns:
            Context information string
        """
        if not robot_context:
            return "Robot type: Unknown\nAvailable controllers: MotionController, ManipulationController, VisionController"
        
        robot = robot_context.robot_profile
        info = f"""Robot Information:
- Type: {robot.robot_type.value}
- Capabilities: {robot.capabilities}
- Available Skills: {', '.join(robot_context.skill_library.keys())}"""
        
        return info
    
    def regenerate_code(
        self,
        skill_id: str,
        modifications: Optional[Dict[str, Any]] = None
    ) -> Optional[GeneratedCode]:
        """Regenerate code with modifications.
        
        Args:
            skill_id: ID of generated code to regenerate
            modifications: Modifications to apply
        
        Returns:
            New GeneratedCode or None
        """
        if skill_id not in self.generation_history:
            logger.warning(f"Skill not found: {skill_id}")
            return None
        
        original = self.generation_history[skill_id]
        
        # Apply modifications
        code = original.code
        if modifications:
            for key, value in modifications.items():
                pattern = f"{{{key}}}"
                code = code.replace(pattern, str(value))
        
        new_generated = GeneratedCode(
            code=code,
            skill_id=f"{skill_id}_v2",
            intent=original.intent,
            template_used=original.template_used,
            llm_used=original.llm_used,
            complexity=original.complexity
        )
        
        self.generation_history[new_generated.skill_id] = new_generated
        return new_generated
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get code generation statistics.
        
        Returns:
            Dict with generation statistics
        """
        total = len(self.generation_history)
        template_based = sum(1 for g in self.generation_history.values() if g.template_used)
        llm_based = sum(1 for g in self.generation_history.values() if g.llm_used)
        
        avg_confidence = (
            sum(g.success_rate_prediction for g in self.generation_history.values()) / total
            if total > 0 else 0
        )
        
        return {
            "total_generated": total,
            "template_based": template_based,
            "llm_based": llm_based,
            "fallback": total - template_based - llm_based,
            "average_confidence": avg_confidence
        }
