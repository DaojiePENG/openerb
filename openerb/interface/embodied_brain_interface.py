"""
Embodied Robot Brain Interface - Main User Interaction Layer

This is the PRIMARY entry point for users to interact with OpenERB.
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from loguru import logger

from openerb.modules.prefrontal_cortex import PrefrontalCortex
from openerb.modules.motor_cortex import MotorCortex
from openerb.modules.cerebellum import Cerebellum
from openerb.modules.hippocampus import Hippocampus
from openerb.modules.limbic_system import SafetyEvaluator, DangerAssessor
from openerb.modules.insular_cortex import InsularCortex
from openerb.modules.visual_cortex import VisualCortex
from openerb.modules.system_integration import IntegrationEngine
from openerb.core.types import (
    UserProfile, Skill, Intent, RobotType, SkillType, ExecutionResult, RobotContext
)
from openerb.llm.config import LLMConfig


class EmbodiedBrainInterface:
    """Main user interface for the embodied robot brain."""

    def __init__(self, robot_body: Optional[RobotType] = None):
        """Initialize the embodied brain interface."""
        self.console = Console()
        self.robot_body = robot_body or RobotType.G1
        self.user: Optional[UserProfile] = None
        self.user_id: Optional[str] = None
        
        # Initialize all neural modules
        self._init_modules()
        
        # Session state
        self.conversation_history: List[Dict[str, str]] = []
        self.session_start = datetime.now()
        self.robot_context: Optional[RobotContext] = None
        
        logger.info(f"🧠 Embodied Brain Interface initialized for {self.robot_body.value}")
        
    def _init_modules(self):
        """Initialize all neural system modules."""
        try:
            self.llm_client = LLMConfig.create_client()
            self.llm_available = True
        except Exception as e:
            logger.warning(f"LLM unavailable: {e}")
            self.llm_client = None
            self.llm_available = False
        
        # Initialize core modules
        self.prefrontal_cortex = self._safe_init(
            lambda: PrefrontalCortex(
                llm_client=self.llm_client,
                max_conversation_history=50
            ),
            "PrefrontalCortex"
        )
        
        self.motor_cortex = self._safe_init(
            lambda: MotorCortex(robot_type=self.robot_body, simulation_mode=True),
            "MotorCortex"
        )
        
        self.cerebellum = self._safe_init(lambda: Cerebellum(), "Cerebellum")
        self.hippocampus = self._safe_init(lambda: Hippocampus(), "Hippocampus")
        self.safety_evaluator = self._safe_init(lambda: SafetyEvaluator(), "SafetyEvaluator")
        self.danger_assessor = self._safe_init(lambda: DangerAssessor(), "DangerAssessor")
        
        self.insular_cortex = self._safe_init(lambda: InsularCortex(), "InsularCortex")
        if self.insular_cortex:
            try:
                self.insular_cortex.identify_robot(self.robot_body.value)
            except Exception as e:
                logger.warning(f"Could not identify robot: {e}")
        
        self.visual_cortex = self._safe_init(lambda: VisualCortex(), "VisualCortex")
        self.integration_engine = self._safe_init(lambda: IntegrationEngine(), "IntegrationEngine")
    
    def _safe_init(self, init_func, name: str):
        """Safely initialize a module."""
        try:
            return init_func()
        except Exception as e:
            logger.warning(f"{name} init failed: {e}")
            return None

    async def start(self):
        """Start the interactive chat session."""
        self._print_welcome()
        await self._setup_user()
        self._print_system_status()
        await self._chat_loop()
        self._print_goodbye()

    def _print_welcome(self):
        """Print welcome message."""
        self.console.print(Panel.fit(
            "[bold cyan]🤖 Welcome[/bold cyan]\n\n"
            "[cyan]🧠 OpenERB - Embodied Robot Brain[/cyan]\n"
            "[cyan]Integrated Neural System[/cyan]\n\n"
            "[cyan]I am a learning system that can:\n"
            "  • Remember who you are\n"
            "  • Learn new skills from conversation\n"
            "  • Generate and execute code\n"
            "  • Understand what body I'm on\n"
            "  • Make intelligent decisions[/cyan]"
        ))

    async def _setup_user(self):
        """Set up user profile."""
        name_input = input("\n👤 Who am I talking with?\nYour name: ").strip()
        
        if name_input:
            self.user = UserProfile(
                user_id=str(uuid.uuid4()),
                name=name_input
            )
            self.user_id = self.user.user_id
            self.console.print(f"✓ Nice to meet you, {self.user.name}!")
            logger.info(f"Created user profile for {self.user.name}")
            
            # Store in Hippocampus
            if self.hippocampus:
                try:
                    self.hippocampus.save_user_profile(self.user)
                except Exception as e:
                    logger.debug(f"Could not save profile: {e}")

    def _print_system_status(self):
        """Print system status."""
        table = Table(title="🤖 System Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row("Robot Body", self.robot_body.value)
        
        if self.insular_cortex:
            try:
                profile = self.insular_cortex.get_robot_profile()
                dof = profile.get('dof', 'N/A')
                gripper = profile.get('has_gripper', False)
                table.add_row("DOF", str(dof))
                table.add_row("Gripper", "Yes" if gripper else "No")
            except:
                pass
        
        table.add_row("LLM", "✅ Available" if self.llm_available else "❌ Unavailable")
        table.add_row("Memory System", "✅ Active" if self.hippocampus else "❌ Inactive")
        table.add_row("Skill Library", "✅ Active" if self.cerebellum else "❌ Inactive")
        
        self.console.print("\n" + table.title + "\n")
        self.console.print(table)
        self.console.print()

    def _print_help(self):
        """Print help message."""
        self.console.print("\n[cyan]Available commands:[/cyan]")
        self.console.print("  help              - Show this message")
        self.console.print("  skills            - Show learned skills")
        self.console.print("  who am i          - Show user profile")
        self.console.print("  quit/exit         - Exit chat")
        self.console.print("\n[cyan]Examples:[/cyan]")
        self.console.print("  learn to add two numbers")
        self.console.print("  teach me how to move forward")
        self.console.print("  what can you do\n")

    async def _chat_loop(self):
        """Main interactive chat loop."""
        self.console.print("[cyan]Type 'help' for commands, 'quit' to exit.\n[/cyan]")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["quit", "exit", "bye"]:
                    break
                
                # Normalize input
                user_lower = user_input.lower().rstrip('?!., ')
                
                # Built-in commands
                if user_lower == "help":
                    self._print_help()
                    continue
                
                if any(phrase in user_lower for phrase in ["skills", "what can you do", "capabilities"]):
                    await self._list_skills()
                    continue
                
                if any(phrase in user_lower for phrase in ["who am i", "remember", "memories"]):
                    self._print_user_stats()
                    continue
                
                # Process through brain
                await self._process_user_input(user_input)
                
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                logger.exception("Chat loop error")

    async def _process_user_input(self, user_input: str):
        """Process user input through neural modules."""
        user_lower = user_input.lower()
        
        # Check for action keywords
        action_keywords = ["learn", "teach", "execute", "run", "do", "make", "can you", "help me"]
        is_likely_action = any(kw in user_lower for kw in action_keywords)
        
        if not self.prefrontal_cortex:
            self.console.print("[cyan]Brain not available. Try a simpler request.[/cyan]")
            return
        
        try:
            self.console.print("[dim]🧠 Processing...[/dim]")
            result = await self.prefrontal_cortex.process_input(
                text=user_input,
                user=self.user
            )
            
            if result and result.intents:
                intent = result.intents[0]
                logger.info(f"Intent: {intent.action} ({intent.confidence:.2f})")
                
                if is_likely_action or intent.confidence > 0.8:
                    await self._handle_action(intent, user_input)
                else:
                    await self._respond_to_query(intent, user_input)
            else:
                if is_likely_action:
                    # Create synthetic intent
                    intent = Intent(
                        raw_text=user_input,
                        action="learn" if "learn" in user_lower or "teach" in user_lower else "execute",
                        parameters={"task": user_input},
                        confidence=0.7
                    )
                    await self._handle_action(intent, user_input)
                else:
                    self.console.print("[cyan]Tell me more about what you mean.[/cyan]")
        
        except Exception as e:
            logger.error(f"Error: {e}")
            self.console.print(f"[yellow]I'm having trouble understanding that. {e}[/yellow]")

    async def _handle_action(self, intent: Intent, user_input: str):
        """Handle action requests."""
        if not self.motor_cortex:
            self.console.print("[yellow]Can't execute actions right now.[/yellow]")
            return
        
        self.console.print("[yellow]Let me generate code for this...[/yellow]")
        
        try:
            result = await self.motor_cortex.process_intent(
                intent=intent,
                robot_context=self.robot_context,
                prefer_template=True
            )
            
            if result.get('success'):
                self.console.print("[green]✓ Successfully generated and executed![/green]")
                
                # Extract and display execution result
                exec_result = result.get('execution_result')
                if exec_result:
                    # If it's an ExecutionResult object
                    if hasattr(exec_result, 'output') and exec_result.output:
                        output_text = exec_result.output.strip()
                        # Try to extract the final answer from output
                        if 'Answer:' in output_text:
                            # Extract the answer line
                            for line in output_text.split('\n'):
                                if 'Answer:' in line:
                                    self.console.print(f"[cyan]{line}[/cyan]")
                                    break
                        elif 'Result:' in output_text or 'result' in output_text.lower():
                            # Show result lines
                            for line in output_text.split('\n'):
                                if line.strip() and ('result' in line.lower() or 'answer' in line.lower() or '=' in line):
                                    self.console.print(f"[cyan]{line}[/cyan]")
                        else:
                            self.console.print(f"[cyan]{output_text}[/cyan]")
                    else:
                        # Try converting to string if it has useful info
                        exec_str = str(exec_result)
                        if exec_str and 'success=True' in exec_str:
                            self.console.print("[cyan]✓ Task completed successfully[/cyan]")
            else:
                error = result.get('error', 'Failed')
                self.console.print(f"[yellow]Failed: {error}[/yellow]")
        
        except Exception as e:
            logger.error(f"Action failed: {e}")
            self.console.print(f"[yellow]Error: {e}[/yellow]")

    async def _respond_to_query(self, intent: Intent, user_input: str):
        """Respond to conversational queries."""
        self.console.print(f"[cyan]That's an interesting question about '{intent.action}'.[/cyan]")

    async def _list_skills(self):
        """List learned skills."""
        if not self.cerebellum:
            self.console.print("[yellow]Skill library not available.[/yellow]")
            return
        
        try:
            skills = self.cerebellum.list_skills(robot_type=self.robot_body)
            if not skills:
                self.console.print("[yellow]I haven't learned any skills yet.[/yellow]")
                return
            
            table = Table(title="Learned Skills")
            table.add_column("Skill", style="cyan")
            table.add_column("Type", style="green")
            
            for skill in skills:
                if isinstance(skill, dict):
                    name = skill.get('name', 'Unknown')
                    skill_type = skill.get('skill_type', 'N/A')
                else:
                    name = getattr(skill, 'name', str(skill))
                    skill_type = getattr(skill, 'skill_type', 'N/A')
                table.add_row(name, str(skill_type))
            
            self.console.print(table)
        except Exception as e:
            logger.warning(f"Error listing skills: {e}")

    def _print_user_stats(self):
        """Display user information."""
        if not self.user:
            self.console.print("[yellow]User profile not set.[/yellow]")
            return
        
        table = Table(title="👤 User Profile")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Name", self.user.name or "Unknown")
        table.add_row("User ID", self.user_id or "Not set")
        table.add_row("Session Start", self.session_start.strftime("%Y-%m-%d %H:%M:%S"))
        
        if self.hippocampus and self.user_id:
            try:
                profile = self.hippocampus.get_user_profile(self.user_id)
                if profile:
                    skills_known = getattr(profile, 'skill_progress', {})
                    table.add_row("Skills Learned", str(len(skills_known) if skills_known else 0))
            except Exception as e:
                logger.debug(f"Error getting stats: {e}")
        
        self.console.print(table)

    def _print_goodbye(self):
        """Print goodbye message."""
        self.console.print("\nThank you for learning with me" + (f", {self.user.name}" if self.user else "") + "!")
        if self.user:
            self.console.print("\nI'll remember:")
            self.console.print("  • Your name and preferences")
            self.console.print("  • Skills we practiced together")
            self.console.print("  • Our conversations")
            self.console.print("\nNext time you visit, I'll recognize you!")
        self.console.print("\n👋 Goodbye!\n")

    def _record_interaction(self, user_input: str, result):
        """Record interaction in memory."""
        self.conversation_history.append({
            "user_input": user_input,
            "timestamp": datetime.now().isoformat(),
            "intents": [i.action for i in result.intents] if result and result.intents else []
        })


async def start_embodied_brain(robot_body: Optional[RobotType] = None):
    """Main entry point for starting the embodied brain interface."""
    interface = EmbodiedBrainInterface(robot_body=robot_body)
    await interface.start()


if __name__ == "__main__":
    asyncio.run(start_embodied_brain(robot_body=RobotType.G1))
