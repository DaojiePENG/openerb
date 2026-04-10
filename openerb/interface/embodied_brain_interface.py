"""
Embodied Robot Brain Interface - Main User Interaction Layer

This is the PRIMARY entry point for users to interact with OpenERB.

Architecture:
  1. Conversational layer (LLM chat) - basic cortex function, always available
  2. Intent recognition layer - classify whether user needs action or just chat
  3. Action layer - code generation/execution via MotorCortex for robot tasks

The brain should FIRST be a good conversationalist, THEN handle robot tasks.
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
from rich.markdown import Markdown
from loguru import logger

from openerb.modules.prefrontal_cortex import PrefrontalCortex
from openerb.modules.motor_cortex import MotorCortex
from openerb.modules.cerebellum import Cerebellum
from openerb.modules.hippocampus import Hippocampus
from openerb.modules.limbic_system import SafetyEvaluator, DangerAssessor
from openerb.modules.insular_cortex import InsularCortex
from openerb.modules.visual_cortex import VisualCortex
from openerb.modules.system_integration import IntegrationEngine
from openerb.llm.base import Message
from openerb.core.types import (
    UserProfile, Skill, Intent, RobotType, SkillType, ExecutionResult, RobotContext
)
from openerb.llm.config import LLMConfig
from openerb.prompts import load_prompt


class EmbodiedBrainInterface:
    """Main user interface for the embodied robot brain."""

    # Persistent user profiles path (sibling to skill_library.json)
    _USER_PROFILES_PATH = Path(__file__).resolve().parent.parent / "data" / "user_profiles.json"

    def __init__(self, robot_body: Optional[RobotType] = None):
        """Initialize the embodied brain interface."""
        self.console = Console()
        self.robot_body = robot_body or RobotType.G1
        self.user: Optional[UserProfile] = None
        self.user_id: Optional[str] = None
        self._is_returning_user: bool = False
        
        # Initialize all neural modules
        self._init_modules()
        
        # Session state
        self.conversation_history: List[Dict[str, str]] = []
        self.session_start = datetime.now()
        self.robot_context: Optional[RobotContext] = None
        
        # Chat context for LLM conversations - maintains multi-turn history
        self._chat_messages: List[Message] = []
        self._init_chat_system_prompt()
        
        logger.info(f"🧠 Embodied Brain Interface initialized for {self.robot_body.value}")
    
    def _init_chat_system_prompt(self):
        """Initialize the system prompt template for conversational chat.
        
        Loads the prompt template from prompts/chat_system.md and fills
        in runtime placeholders (except skill_summary, which is filled
        dynamically per call in _chat_with_llm).
        """
        robot_info = f"Robot body: {self.robot_body.value}"
        if self.insular_cortex:
            try:
                profile = self.insular_cortex.get_robot_profile()
                robot_info += f", DOF: {profile.get('dof', '?')}, Gripper: {profile.get('has_gripper', False)}"
            except:
                pass
        
        user_name = self.user.name if self.user else "the user"
        user_status = "returning user (old friend, you've chatted before)" if self._is_returning_user else "new user (first meeting)"
        past_summaries = self._get_past_summaries_for_prompt()
        
        template = load_prompt("chat_system")
        # Fill static placeholders; leave {skill_summary} for dynamic fill per call
        self._system_prompt_template = template.format(
            robot_body=self.robot_body.value,
            robot_info=robot_info,
            user_name=user_name,
            user_status=user_status,
            conversation_history=past_summaries if past_summaries else "No previous conversations recorded.",
            skill_summary="{skill_summary}",
        )

    def _get_skill_summary(self) -> str:
        """Build a fresh skill inventory string from the Cerebellum.
        
        Called before each LLM call to ensure the prompt reflects the
        latest skills (which may have been added or removed).
        """
        if not self.cerebellum:
            return "Skill library not available."
        
        try:
            skills = self.cerebellum.list_skills(robot_type=self.robot_body)
            if not skills:
                return "Skill library is empty — no skills learned yet."
            
            lines = []
            for skill in skills:
                if isinstance(skill, dict):
                    name = skill.get('name', 'Unknown')
                    desc = skill.get('description', '')
                    lines.append(f"- {name}: {desc}")
                else:
                    lines.append(f"- {getattr(skill, 'name', str(skill))}")
            return "\n".join(lines)
        except Exception as e:
            logger.debug(f"Error building skill summary: {e}")
            return "Skill library unavailable."

    def _init_modules(self):
        """Initialize all neural system modules."""
        # Main LLM client for conversation and intent recognition
        try:
            self.llm_client = LLMConfig.create_client()
            self.llm_available = True
        except Exception as e:
            logger.warning(f"LLM unavailable: {e}")
            self.llm_client = None
            self.llm_available = False
        
        # Dedicated LLM client for code generation (can use a different model)
        try:
            import os
            code_model = os.getenv("LLM_CODE_MODEL", os.getenv("LLM_MODEL", "qwen3.6-plus"))
            self.code_llm_client = LLMConfig.create_client(model=code_model)
        except Exception as e:
            logger.warning(f"Code LLM unavailable, will share main LLM: {e}")
            self.code_llm_client = self.llm_client
        
        # Initialize core modules
        self.prefrontal_cortex = self._safe_init(
            lambda: PrefrontalCortex(
                llm_client=self.llm_client,
                max_conversation_history=50
            ),
            "PrefrontalCortex"
        )
        
        self.motor_cortex = self._safe_init(
            lambda: MotorCortex(
                llm_client=self.code_llm_client,
                robot_type=self.robot_body,
                simulation_mode=True
            ),
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
        try:
            await self._chat_loop()
        except KeyboardInterrupt:
            self.console.print("\n[dim]Interrupted...[/dim]")
        # Always summarize & save on exit
        await self._summarize_and_save_session()
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

    # ── User profile persistence ──────────────────────────────────

    def _load_user_profiles(self) -> Dict[str, Any]:
        """Load all persisted user profiles from JSON."""
        try:
            if self._USER_PROFILES_PATH.exists():
                return json.loads(self._USER_PROFILES_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not load user profiles: {e}")
        return {}

    def _save_user_profiles(self, profiles: Dict[str, Any]):
        """Atomically save user profiles to JSON."""
        try:
            self._USER_PROFILES_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._USER_PROFILES_PATH.with_suffix(".tmp")
            tmp.write_text(json.dumps(profiles, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self._USER_PROFILES_PATH)
        except Exception as e:
            logger.error(f"Could not save user profiles: {e}")

    def _find_profile_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Look up a persisted profile by name (case-insensitive)."""
        profiles = self._load_user_profiles()
        name_lower = name.lower()
        for uid, data in profiles.items():
            if data.get("name", "").lower() == name_lower:
                return data
        return None

    def _persist_current_user(self):
        """Write current user profile to disk."""
        if not self.user:
            return
        profiles = self._load_user_profiles()
        profiles[self.user_id] = {
            "user_id": self.user_id,
            "name": self.user.name,
            "created_at": self.user.created_at.isoformat(),
            "last_seen": datetime.now().isoformat(),
            "session_count": profiles.get(self.user_id, {}).get("session_count", 0) + 1,
            "total_interactions": profiles.get(self.user_id, {}).get("total_interactions", 0),
            "preferences": self.user.preferences,
        }
        self._save_user_profiles(profiles)

    def _update_interaction_count(self):
        """Increment total_interactions for the current user."""
        if not self.user:
            return
        profiles = self._load_user_profiles()
        if self.user_id in profiles:
            profiles[self.user_id]["total_interactions"] = profiles[self.user_id].get("total_interactions", 0) + 1
            profiles[self.user_id]["last_seen"] = datetime.now().isoformat()
            self._save_user_profiles(profiles)

    async def _setup_user(self):
        """Set up user profile — restores returning users from disk."""
        name_input = input("\n👤 Who am I talking with?\nYour name: ").strip()
        
        if name_input:
            existing = self._find_profile_by_name(name_input)
            if existing:
                # Returning user → restore profile
                self.user = UserProfile(
                    user_id=existing["user_id"],
                    name=existing.get("name", name_input),
                    preferences=existing.get("preferences", {}),
                )
                try:
                    self.user.created_at = datetime.fromisoformat(existing["created_at"])
                except Exception:
                    pass
                self.user_id = self.user.user_id
                self._is_returning_user = True
                session_count = existing.get("session_count", 0) + 1
                self.console.print(f"✓ Welcome back, {self.user.name}! 🎉 We've chatted {session_count} times — old friends!")
                logger.info(f"Restored returning user: {self.user.name} (sessions={session_count})")
            else:
                # New user
                self.user = UserProfile(
                    user_id=str(uuid.uuid4()),
                    name=name_input,
                )
                self.user_id = self.user.user_id
                self._is_returning_user = False
                self.console.print(f"✓ Nice to meet you, {self.user.name}!")
                logger.info(f"Created user profile for {self.user.name}")
            
            # Persist to disk
            self._persist_current_user()
            
            # Refresh system prompt with user name
            self._init_chat_system_prompt()

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
        self.console.print("  quit/exit         - Exit chat")
        self.console.print("\n[cyan]You can also ask me naturally:[/cyan]")
        self.console.print("  what can you do?  - I'll show my skill library")
        self.console.print("  who am I?         - I'll show your profile")
        self.console.print("  calculate 1+1     - I'll generate & execute code")
        self.console.print("  move forward      - I'll try to control the robot\n")

    async def _chat_loop(self):
        """Main interactive chat loop."""
        self.console.print("[cyan]Type 'help' for commands, 'quit' or Ctrl+C to exit.\n[/cyan]")
        
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
                
                # Process through brain
                await self._process_user_input(user_input)
                
            except EOFError:
                break
            except KeyboardInterrupt:
                raise  # Propagate to start() for graceful shutdown
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                logger.exception("Chat loop error")

    async def _process_user_input(self, user_input: str):
        """Process user input - conversation first, action when needed.
        
        Flow:
        1. Send user input to LLM for conversational response
        2. If LLM signals [ACTION_REQUIRED] or [CODE_REQUIRED], route to motor cortex
        3. Otherwise, display the conversational response directly
        
        Behavior constraints (e.g. always route math to action) are enforced
        via the system prompt in prompts/chat_system.md, NOT via client-side hacks.
        """
        if not self.llm_client:
            self.console.print("[yellow]LLM not available. I can only handle basic commands.[/yellow]")
            return
        
        try:
            self.console.print("[dim]🧠 Thinking...[/dim]")
            
            # Update system prompt template with current user info
            if self.user and f"User name: {self.user.name}" not in self._system_prompt_template:
                self._system_prompt_template += f"\nUser name: {self.user.name}"
            
            # Add user message to chat history
            self._chat_messages.append(Message(role="user", content=user_input))
            
            # Call LLM for natural conversation
            response = await self._chat_with_llm(user_input)
            
            if not response:
                self.console.print("[yellow]I'm having trouble thinking right now. Try again?[/yellow]")
                return
            
            # Parse marker from LLM response
            marker = self._extract_marker(response)
            
            if marker in ("ACTION_REQUIRED", "CODE_REQUIRED"):
                # Don't print LLM acknowledgment here — _handle_action_request
                # will print the final interpreted result to avoid double response
                self.console.print("[yellow]🔧 Let me work on that...[/yellow]")
                await self._handle_action_request(user_input)
            elif marker == "LIST_SKILLS":
                clean_response = response.replace("[LIST_SKILLS]", "").replace("[CHAT]", "").strip()
                if clean_response:
                    self.console.print(f"[cyan]{clean_response}[/cyan]")
                await self._list_skills()
                self._chat_messages.append(Message(
                    role="assistant",
                    content="[I displayed the skill library table to the user. I do not know the contents — I must use [LIST_SKILLS] again if asked.]"
                ))
            elif marker == "USER_PROFILE":
                clean_response = response.replace("[USER_PROFILE]", "").replace("[CHAT]", "").strip()
                if clean_response:
                    self.console.print(f"[cyan]{clean_response}[/cyan]")
                self._print_user_stats()
                self._chat_messages.append(Message(
                    role="assistant",
                    content="[I displayed the user profile table to the user. I must use [USER_PROFILE] again if asked.]"
                ))
            elif marker == "LEARNING_PROGRESS":
                clean_response = response.replace("[LEARNING_PROGRESS]", "").replace("[CHAT]", "").strip()
                if clean_response:
                    self.console.print(f"[cyan]{clean_response}[/cyan]")
                await self._show_learning_progress()
                self._chat_messages.append(Message(
                    role="assistant",
                    content="[I displayed the learning progress report to the user.]"
                ))
            else:
                # No action marker — display as conversation
                clean_response = response.replace("[CHAT]", "").strip()
                self.console.print(f"[cyan]{clean_response}[/cyan]")
                self._chat_messages.append(Message(role="assistant", content=clean_response))
            
            # Record interaction
            self.conversation_history.append({
                "user_input": user_input,
                "response": response,
                "timestamp": datetime.now().isoformat(),
            })
            self._update_interaction_count()
            
            # Keep chat history manageable (last 40 turns)
            if len(self._chat_messages) > 80:
                # Keep system context + last 40 exchanges
                self._chat_messages = self._chat_messages[-80:]
        
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            self.console.print(f"[yellow]Sorry, I encountered an error: {e}[/yellow]")

    def _extract_marker(self, response: str) -> Optional[str]:
        """Extract the routing marker from the LLM response.
        
        First checks if the LLM included an explicit marker.
        If not, falls back to intent inference from the user's last message
        to compensate for model non-compliance.
        
        Returns:
            Marker name (e.g. 'ACTION_REQUIRED', 'LIST_SKILLS') or None for chat.
        """
        import re
        
        # 1. Check for explicit markers in response
        markers = ["ACTION_REQUIRED", "CODE_REQUIRED", "LIST_SKILLS", "USER_PROFILE", "LEARNING_PROGRESS"]
        for m in markers:
            if f"[{m}]" in response:
                return m
        
        # 2. Fallback: infer from the user's last input
        #    This compensates when the LLM ignores the structured format.
        if not self._chat_messages:
            return None
        
        last_user_msg = None
        for msg in reversed(self._chat_messages):
            if msg.role == "user":
                last_user_msg = msg.content.lower()
                break
        
        if not last_user_msg:
            return None
        
        # Skill listing patterns
        skill_patterns = [
            r'skill|能力|技能|你会什么|what can you do|show.*(skill|能力)',
            r'能力列表|技能列表|skills?\s*list',
        ]
        for pat in skill_patterns:
            if re.search(pat, last_user_msg):
                logger.debug(f"Marker fallback: LIST_SKILLS (input matched '{pat}')")
                return "LIST_SKILLS"
        
        # Learning progress patterns (MUST come before action patterns so 学习进度 isn't caught by 学习.{2,})
        learning_progress_patterns = [
            r'学习进度|学习状态|掌握.*程度|mastery|competenc',
            r'learning.*(progress|status|report)',
            r'我.*掌握|学了什么|what.*i.*learn',
        ]
        for pat in learning_progress_patterns:
            if re.search(pat, last_user_msg):
                logger.debug(f"Marker fallback: LEARNING_PROGRESS (input matched '{pat}')")
                return "LEARNING_PROGRESS"
        
        # Computation / action patterns
        action_patterns = [
            r'\d+\s*[+\-*/^%]\s*\d+',            # math: 9*9, 1+1
            r'calculat|计算|compute',               # explicit calc
            r'fibonacci|斐波那契|factorial|阶乘',   # algorithms
            r'生成|输出.*\d|排序|sort',              # generation/output
            r'move|walk|grasp|grab|前进|移动|抓取',  # robot control
            r'learn\s+to\b',                        # English: learn to ...
            r'学习.*技能|learn.*skill',              # learn a skill
            r'学习.{2,}',                           # learn to do anything (Chinese)
            r'绘制|画.*图|draw|plot|paint',          # drawing/plotting
            r'保存.*图|save.*image|save.*file',      # save output to file
            r'print\s+\d+|print\s+\w+.*\bint|输出\s*\d+',  # print N items
            r'generate\s+\w|create\s+\w|produce\s+\w',      # generate/create something
        ]
        for pat in action_patterns:
            if re.search(pat, last_user_msg):
                logger.debug(f"Marker fallback: ACTION_REQUIRED (input matched '{pat}')")
                return "ACTION_REQUIRED"
        
        # User profile
        if re.search(r'who am i|my profile|我的信息|我的资料|个人信息|profile|你认识我|你记得我', last_user_msg):
            return "USER_PROFILE"
        
        # Learning progress
        if re.search(r'学习进度|学习状态|掌握.*程度|mastery|competenc|learning.*(progress|status|report)|我.*掌握|学了什么', last_user_msg):
            return "LEARNING_PROGRESS"
        
        return None

    async def _chat_with_llm(self, user_input: str) -> Optional[str]:
        """Have a natural conversation with the user via LLM.
        
        This is the core "cerebral cortex" function - natural language
        understanding and generation. The system prompt is rebuilt each
        call with a fresh skill inventory.
        
        Args:
            user_input: The user's message (may or may not be in _chat_messages already)
        """
        try:
            # Build system prompt with fresh skill inventory
            system_prompt = self._system_prompt_template.format(
                skill_summary=self._get_skill_summary()
            )
            
            # Build messages: system prompt + conversation history
            messages = [Message(role="system", content=system_prompt)]
            messages.extend(self._chat_messages)
            
            # Ensure the last message is from the user
            if not self._chat_messages or self._chat_messages[-1].content != user_input:
                messages.append(Message(role="user", content=user_input))
            
            response = await self.llm_client.call(
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
            )
            
            return response.content.strip() if response and response.content else None
        
        except Exception as e:
            logger.error(f"LLM chat failed: {e}")
            return None

    async def _handle_action_request(self, user_input: str):
        """Handle requests that need code generation/execution.
        
        Flow:
        1. Parse intent via PrefrontalCortex
        2. Search Cerebellum for existing skill (reuse if found)
        3. If no existing skill, generate + execute via MotorCortex
        4. On success, persist skill to Cerebellum + record in Hippocampus
        """
        if not self.motor_cortex:
            self.console.print("[yellow]Motor cortex not available. Can't execute actions.[/yellow]")
            return
        
        try:
            # 1. Parse intent
            intent = None
            if self.prefrontal_cortex:
                try:
                    result = await self.prefrontal_cortex.process_input(
                        text=user_input, user=self.user
                    )
                    if result and result.intents:
                        intent = result.intents[0]
                        logger.info(f"Intent: {intent.action} ({intent.confidence:.2f})")
                except Exception as e:
                    logger.warning(f"Intent parsing failed: {e}")
            
            if not intent:
                # Derive a meaningful skill name from user input
                skill_name = self._derive_skill_name(user_input)
                intent = Intent(
                    raw_text=user_input,
                    action=skill_name,
                    parameters={"task": user_input},
                    confidence=0.6
                )
            else:
                # Always override with derived skill name when PrefrontalCortex
                # returns a generic/ambiguous action. The derived name is based on
                # keyword analysis and is more specific for skill matching.
                derived_name = self._derive_skill_name(user_input)
                _GENERIC_ACTIONS = {
                    "calculate", "compute", "general_task", "learn", "execute",
                    "do", "perform", "run", "print", "show", "generate", "create",
                    "make", "build", "write", "output",
                }
                if intent.action.lower() in _GENERIC_ACTIONS:
                    logger.info(f"Overriding generic intent '{intent.action}' → '{derived_name}'")
                    intent = Intent(
                        raw_text=user_input,
                        action=derived_name,
                        parameters=intent.parameters,
                        confidence=intent.confidence,
                    )
                elif intent.raw_text != user_input:
                    # PrefrontalCortex sets raw_text=action, fix to original user input
                    intent = Intent(
                        raw_text=user_input,
                        action=intent.action,
                        parameters=intent.parameters,
                        confidence=intent.confidence,
                    )
            
            # 2. Check Cerebellum for existing skill
            existing_skill = await self._find_existing_skill(intent)
            if existing_skill:
                skill_name = existing_skill.get('name', 'unknown')
                skill_id = existing_skill.get('id', '?')
                self.console.print(f"[dim]📚 Found existing skill: [bold]{skill_name}[/bold] (id: {skill_id}), reusing...[/dim]")
                # Try to re-parameterize the skill for the new input
                adapted_code = await self._reparameterize_skill(existing_skill, user_input)
                if adapted_code:
                    self.console.print(f"[dim]  └─ 🔧 Adapted parameters for: {user_input}[/dim]")
                result = self._execute_existing_skill(existing_skill, adapted_code)
                skill_reused = True
                execution_method = f"♻️ Reused skill: {skill_name}" + (" (adapted)" if adapted_code else "")
            else:
                self.console.print("[dim]🆕 No existing skill found, generating new code...[/dim]")
                # 3. Generate and execute via MotorCortex
                result = await self.motor_cortex.process_intent(
                    intent=intent,
                    robot_context=self.robot_context,
                    prefer_template=False
                )
                skill_reused = False
                gen_code = result.get('generated_code')
                gen_method = getattr(gen_code, 'llm_used', False) if gen_code else False
                execution_method = "🤖 LLM-generated code" if gen_method else "📝 Template/fallback code"
            
            # ── Failure-driven refinement loop ──
            # If execution fails, retry with error feedback (up to 2 retries)
            refinement_attempts = 0
            max_refinements = 2
            while not result.get('success') and not skill_reused and refinement_attempts < max_refinements:
                refinement_attempts += 1
                error = result.get('error', 'Unknown error')
                self.console.print(
                    f"[yellow]⚠ Attempt failed: {error}[/yellow]\n"
                    f"[dim]  └─ 🔄 Refining... (attempt {refinement_attempts}/{max_refinements})[/dim]"
                )
                # Record the failure in Hippocampus for analytics
                self._record_execution_failure(intent, result)
                # Retry with error feedback
                result = await self.motor_cortex.process_intent(
                    intent=intent,
                    robot_context=self.robot_context,
                    prefer_template=False,
                )
                execution_method = f"🔄 Refined code (attempt {refinement_attempts + 1})"

            if result.get('success'):
                exec_result = result.get('execution_result')
                output = ""
                if exec_result and hasattr(exec_result, 'output') and exec_result.output:
                    output = exec_result.output.strip()
                
                exec_time = f"{exec_result.execution_time:.3f}s" if exec_result and hasattr(exec_result, 'execution_time') else "?"
                
                # Transparency: show execution method
                self.console.print(f"[dim]  └─ Method: {execution_method} | Time: {exec_time}[/dim]")
                if refinement_attempts > 0:
                    self.console.print(f"[green]  └─ ✅ Succeeded after {refinement_attempts} refinement(s)![/green]")
                
                # Feed the execution result back to LLM for a natural response
                natural_reply = await self._interpret_execution_result(
                    user_input, output, execution_method
                )
                
                if natural_reply:
                    self.console.print(f"[cyan]{natural_reply}[/cyan]")
                elif output:
                    self.console.print(f"[cyan]{output}[/cyan]")
                else:
                    self.console.print("[green]✓ Executed successfully.[/green]")
                
                # Record in chat history
                reply_for_history = natural_reply or output or "Task executed successfully."
                self._chat_messages.append(Message(
                    role="assistant",
                    content=reply_for_history
                ))
                
                # 4. Persist new skill to Cerebellum + record in Hippocampus
                if not skill_reused:
                    self._persist_learned_skill(intent, result)
                else:
                    # Update execution stats for reused skill
                    self._record_skill_reuse(existing_skill, result)
                
                # Record success in Hippocampus (including refinement info)
                self._record_execution_success(intent, result, refinement_attempts)
            else:
                error = result.get('error', 'Unknown error')
                self.console.print(f"[yellow]⚠ Execution failed: {error}[/yellow]")
                self.console.print(f"[dim]  └─ Method: {execution_method}[/dim]")
                if refinement_attempts > 0:
                    self.console.print(f"[dim]  └─ Failed after {refinement_attempts} refinement attempt(s)[/dim]")
                # Record final failure in Hippocampus
                self._record_execution_failure(intent, result)
                self._chat_messages.append(Message(
                    role="assistant",
                    content=f"I tried to execute the task but it failed: {error}"
                ))
        
        except Exception as e:
            logger.error(f"Action failed: {e}")
            self.console.print(f"[yellow]Error executing action: {e}[/yellow]")

    def _derive_skill_name(self, user_input: str) -> str:
        """Derive a meaningful skill name from user input.
        
        Converts 'what is 6+9-2?' → 'math_calculation'
        Converts 'generate fibonacci sequence' → 'fibonacci'
        Converts 'calculate 1+1' → 'math_calculation'
        Converts 'learn to draw circle' → 'draw_shape'
        Converts 'learn to print integers' → 'print_integers'
        """
        import re
        text = user_input.lower().strip()
        
        # Remove question markers
        text = re.sub(r'[?？!！。，,.]', '', text)
        
        # Strip "learn to" / "学习" prefix to get to the actual task
        text = re.sub(r'^(learn\s+to\s+|学习)', '', text).strip()
        
        # Detect common patterns — produce stable, reusable names
        if re.search(r'[\d]+\s*[+\-*/^%]\s*[\d]', text) or any(kw in text for kw in ['calculate', '计算', 'compute']):
            return "math_calculation"
        if any(kw in text for kw in ['fibonacci', '斐波那契']):
            return "fibonacci"
        if any(kw in text for kw in ['factorial', '阶乘']):
            return "factorial"
        if any(kw in text for kw in ['prime', '素数', '质数']):
            return "prime_numbers"
        if any(kw in text for kw in ['sort', '排序']):
            return "sort"
        if any(kw in text for kw in ['move', 'walk', '移动', '走', '前进']):
            return "move_forward"
        if any(kw in text for kw in ['grasp', 'grab', 'pick', '抓', '拿']):
            return "grasp_object"
        if any(kw in text for kw in ['draw', 'circle', 'plot', 'chart', '绘制', '画', '圆形', '图形', '图片']):
            return "draw_shape"
        
        # Generic: take key words, remove stop words, join with underscore
        stop_words = {'what', 'is', 'the', 'a', 'an', 'of', 'to', 'how', 'can', 'you',
                       'please', 'me', 'do', 'tell', 'answer', 'learn',
                       '是', '的', '了', '吗', '请', '帮', '我', '一下', '什么', '怎么', '能', '会'}
        words = re.findall(r'[a-z]+|[\u4e00-\u9fff]+', text)
        key_words = [w for w in words if w not in stop_words][:3]
        
        if key_words:
            return '_'.join(key_words)
        return "general_task"

    async def _interpret_execution_result(
        self, user_input: str, code_output: str, method: str
    ) -> Optional[str]:
        """Feed execution result back to LLM for a natural language response.
        
        This is crucial: the robot brain should interpret code output and
        reply to the user naturally, not just dump raw stdout.
        """
        if not self.llm_client:
            return None
        
        try:
            interpret_prompt = f"""The user asked: "{user_input}"

I executed code ({method}) and got this output:
{code_output if code_output else "(no output)"}

Based on the execution result, give a brief, natural response to the user's question.
- If there is output, interpret it and answer the user's original question.
- If there is no output or the output doesn't answer the question, say you executed the task but couldn't get a clear result.
- Keep it concise (1-2 sentences).
- Do NOT include [ACTION_REQUIRED] or [CODE_REQUIRED] markers.
- Reply in the same language the user used."""

            interpreter_system = load_prompt("result_interpreter")
            response = await self.llm_client.call(
                messages=[
                    Message(role="system", content=interpreter_system),
                    Message(role="user", content=interpret_prompt),
                ],
                temperature=0.5,
                max_tokens=256,
            )
            
            if response and response.content:
                reply = response.content.strip()
                # Safety: strip any accidental markers
                reply = reply.replace("[ACTION_REQUIRED]", "").replace("[CODE_REQUIRED]", "").strip()
                return reply
        except Exception as e:
            logger.warning(f"Result interpretation failed: {e}")
        
        return None

    async def _find_existing_skill(self, intent: Intent) -> Optional[Dict[str, Any]]:
        """Search Cerebellum for an existing skill matching the intent.
        
        Returns:
            Skill data dict if a good match is found, None otherwise.
        """
        if not self.cerebellum:
            return None
        
        try:
            # Search by action name and raw text
            search_queries = [intent.action]
            if intent.raw_text and intent.raw_text != intent.action:
                search_queries.append(intent.raw_text)
            
            for query in search_queries:
                results = self.cerebellum.search_skill(
                    query=query,
                    robot_type=self.robot_body,
                )
                if results:
                    # Return the best match - must have code
                    for skill_data in results:
                        skill_id = skill_data.get('id')
                        full_skill = self.cerebellum.get_skill(skill_id)
                        if full_skill and full_skill.get('code'):
                            logger.info(f"Found existing skill: {full_skill.get('name')} ({skill_id})")
                            return full_skill
        except Exception as e:
            logger.warning(f"Skill search failed: {e}")
        
        return None

    def _execute_existing_skill(self, skill_data: Dict[str, Any], adapted_code: Optional[str] = None) -> Dict[str, Any]:
        """Execute an existing skill from the Cerebellum.
        
        Args:
            skill_data: Skill data dict from Cerebellum
            adapted_code: If provided, use this re-parameterized code instead of the stored code
        
        Returns:
            Result dict compatible with MotorCortex.process_intent output.
        """
        code = adapted_code or skill_data.get('code', '')
        
        # Validate before executing
        validation = self.motor_cortex.code_validator.validate(code)
        if not validation.valid:
            logger.warning(f"Cached skill failed validation: {validation.details}")
            return {"success": False, "error": f"Cached skill invalid: {validation.details}"}
        
        # Execute
        exec_result = self.motor_cortex.code_executor.execute(code, globals_dict={})
        return {
            "success": exec_result.success,
            "execution_result": exec_result,
            "error": exec_result.error if not exec_result.success else None,
            "reused_skill": skill_data.get('name', 'unknown'),
        }

    def _persist_learned_skill(self, intent: Intent, result: Dict[str, Any]):
        """Persist a newly generated skill to Cerebellum and record in Hippocampus."""
        generated_code = result.get('generated_code')
        if not generated_code or not hasattr(generated_code, 'code') or not generated_code.code:
            return
        
        # Save to Cerebellum
        if self.cerebellum:
            try:
                skill = Skill(
                    name=intent.action,
                    description=f"{intent.raw_text}",
                    code=generated_code.code,
                    dependencies=[],
                    tags=["auto_generated", "learned"],
                    supported_robots=[self.robot_body],
                    skill_type=SkillType.BODY_SPECIFIC,
                )
                skill_id = self.cerebellum.register_skill(
                    skill=skill,
                    robot_body=self.robot_body,
                    description=f"Learned from: {intent.raw_text}",
                    tags=["auto_generated", "learned", intent.action],
                )
                logger.info(f"💾 Persisted skill '{intent.action}' → {skill_id}")
                self.console.print(f"[yellow]💾 New skill learned and saved: [bold]{intent.action}[/bold] (id: {skill_id})[/yellow]")
                
                # Record in Hippocampus
                if self.hippocampus and self.user_id:
                    try:
                        exec_result = result.get('execution_result')
                        duration = exec_result.execution_time if exec_result and hasattr(exec_result, 'execution_time') else 0.0
                        
                        # Start learning + record execution
                        self.hippocampus.start_learning(self.user_id, skill)
                        self.hippocampus.record_skill_execution(
                            user_id=self.user_id,
                            skill=skill,
                            success=True,
                            duration=duration,
                            result_details=f"First execution from intent: {intent.raw_text}",
                        )
                        logger.info(f"📝 Recorded learning event for '{intent.action}'")
                    except Exception as e:
                        logger.warning(f"Hippocampus recording failed: {e}")
            except Exception as e:
                logger.warning(f"Failed to persist skill: {e}")

    def _record_skill_reuse(self, skill_data: Dict[str, Any], result: Dict[str, Any]):
        """Record execution stats when reusing an existing skill."""
        if not self.cerebellum:
            return
        
        skill_id = skill_data.get('id')
        if not skill_id:
            return
        
        try:
            # Read current counts from the stored skill (not the passed-in copy)
            full_skill = self.cerebellum.get_skill(skill_id) or skill_data
            metadata = full_skill.get('metadata', {})
            
            # Update counts in metadata
            exec_count = metadata.get('execution_count', 0) + 1
            success_count = metadata.get('success_count', 0)
            if result.get('success'):
                success_count += 1
            metadata['execution_count'] = exec_count
            metadata['success_count'] = success_count
            metadata['last_used'] = datetime.now().isoformat()
            
            # Write to BOTH top-level and metadata so list_skills can find it
            self.cerebellum.library.update_skill(
                skill_id,
                {
                    'execution_count': exec_count,
                    'success_count': success_count,
                    'metadata': metadata,
                },
                'execution_update'
            )
            logger.debug(f"Updated execution stats for skill {skill_id}: runs={exec_count}")
        except Exception as e:
            logger.warning(f"Failed to update skill stats: {e}")

    def _record_execution_failure(self, intent: Intent, result: Dict[str, Any]):
        """Record a failed execution in Hippocampus for failure-driven learning."""
        if not self.hippocampus or not self.user_id:
            return
        try:
            error = result.get('error', 'Unknown error')
            skill = Skill(
                name=intent.action,
                description=intent.raw_text,
                code=getattr(result.get('generated_code'), 'code', '') or '',
                dependencies=[],
                tags=["auto_generated"],
                supported_robots=[self.robot_body],
                skill_type=SkillType.BODY_SPECIFIC,
            )
            # Ensure a learning profile entry exists
            profile = self.hippocampus.get_user_profile(self.user_id)
            if not profile:
                self.hippocampus.create_user_profile(
                    self.user_id, self.user.name if self.user else "unknown",
                    self.robot_body
                )
            if skill.skill_id not in (self.hippocampus.get_user_profile(self.user_id).skill_progress or {}):
                self.hippocampus.start_learning(self.user_id, skill)
            exec_result = result.get('execution_result')
            duration = exec_result.execution_time if exec_result and hasattr(exec_result, 'execution_time') else 0.0
            self.hippocampus.record_skill_execution(
                user_id=self.user_id,
                skill=skill,
                success=False,
                duration=duration,
                error_message=error,
                result_details=f"Failed execution: {error}",
            )
            logger.info(f"📝 Recorded failure for '{intent.action}': {error}")
        except Exception as e:
            logger.warning(f"Hippocampus failure recording failed: {e}")

    def _record_execution_success(self, intent: Intent, result: Dict[str, Any], refinement_count: int = 0):
        """Record a successful execution in Hippocampus, noting any refinements."""
        if not self.hippocampus or not self.user_id:
            return
        try:
            exec_result = result.get('execution_result')
            duration = exec_result.execution_time if exec_result and hasattr(exec_result, 'execution_time') else 0.0
            skill = Skill(
                name=intent.action,
                description=intent.raw_text,
                code=getattr(result.get('generated_code'), 'code', '') or '',
                dependencies=[],
                tags=["auto_generated"],
                supported_robots=[self.robot_body],
                skill_type=SkillType.BODY_SPECIFIC,
            )
            profile = self.hippocampus.get_user_profile(self.user_id)
            if not profile:
                self.hippocampus.create_user_profile(
                    self.user_id, self.user.name if self.user else "unknown",
                    self.robot_body
                )
            if skill.skill_id not in (self.hippocampus.get_user_profile(self.user_id).skill_progress or {}):
                self.hippocampus.start_learning(self.user_id, skill)
            details = f"Succeeded"
            if refinement_count > 0:
                details += f" after {refinement_count} refinement(s)"
            self.hippocampus.record_skill_execution(
                user_id=self.user_id,
                skill=skill,
                success=True,
                duration=duration,
                result_details=details,
                context={"refinements": refinement_count},
            )
            logger.info(f"📝 Recorded success for '{intent.action}' (refinements={refinement_count})")
        except Exception as e:
            logger.warning(f"Hippocampus success recording failed: {e}")

    async def _reparameterize_skill(self, skill_data: Dict[str, Any], user_input: str) -> Optional[str]:
        """Re-parameterize an existing skill's code for new input values.

        When a user asks 'calculate 3+7' but the existing skill was learned from
        'calculate 1+1', the code hardcodes old values. This method uses the LLM to
        adapt the code to the new parameters while preserving the reusable function.

        Returns updated code string, or None if re-parameterization fails.
        """
        if not self.llm_client:
            return None

        code = skill_data.get('code', '')
        if not code:
            return None

        try:
            prompt = f"""Here is a previously learned Python skill:

```python
{code}
```

The user now asks: "{user_input}"

Adapt the code so it is called with the user's new values.
Rules:
- Keep the same function definition (same function name and parameters)
- Only change the function CALL at the bottom to use the new values
- The code must print() the result
- Return ONLY the complete Python code, no explanation
- If the existing function already handles the new input, just change the call arguments"""

            response = await self.llm_client.call(
                messages=[
                    Message(role="system", content="You are a code adaptation assistant. Output only Python code."),
                    Message(role="user", content=prompt),
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            if response and response.content:
                from openerb.modules.motor_cortex.code_generator import CodeGenerator
                adapted = CodeGenerator._extract_code_from_response(None, response.content)
                if adapted and len(adapted.strip()) > 10:
                    return adapted
        except Exception as e:
            logger.warning(f"Skill re-parameterization failed: {e}")
        return None

    async def _list_skills(self):
        """List learned skills from the Cerebellum skill library."""
        if not self.cerebellum:
            self.console.print("[yellow]Skill library not available.[/yellow]")
            return
        
        try:
            skills = self.cerebellum.list_skills(robot_type=self.robot_body)
            if not skills:
                self.console.print("[yellow]📚 Skill library is empty — I haven't learned any skills yet.[/yellow]")
                self.console.print("[dim]Try asking me to do something, e.g., 'calculate 1+1' or 'generate fibonacci sequence'[/dim]")
                return
            
            table = Table(title=f"📚 Skill Library ({len(skills)} skills)")
            table.add_column("#", style="dim", width=3)
            table.add_column("Name", style="cyan")
            table.add_column("Description", style="white", max_width=40)
            table.add_column("Type", style="green")
            table.add_column("Source", style="yellow")
            table.add_column("Runs", style="magenta", justify="right")
            table.add_column("Success", style="green", justify="right")
            
            for idx, skill in enumerate(skills, 1):
                if isinstance(skill, dict):
                    name = skill.get('name', 'Unknown')
                    desc = skill.get('description', '')[:40]
                    skill_type = skill.get('skill_type', 'N/A')
                    # Determine source from full skill data
                    full_data = self.cerebellum.get_skill(skill.get('id', ''))
                    metadata = full_data.get('metadata', {}) if full_data else {}
                    tags = full_data.get('tags', []) if full_data else []
                    source = "🤖 learned" if "auto_generated" in tags else "📋 preset"
                    # Read execution count from top-level first, then metadata fallback
                    exec_count = skill.get('execution_count', 0)
                    if exec_count == 0 and metadata:
                        exec_count = metadata.get('execution_count', 0)
                    success_count = full_data.get('success_count', 0) if full_data else 0
                    if success_count == 0 and metadata:
                        success_count = metadata.get('success_count', 0)
                    success_rate = success_count / exec_count if exec_count > 0 else 0.0
                else:
                    name = getattr(skill, 'name', str(skill))
                    desc = getattr(skill, 'description', '')[:40]
                    skill_type = getattr(skill, 'skill_type', 'N/A')
                    exec_count = 0
                    success_rate = 0.0
                    source = "?"
                
                success_str = f"{success_rate:.0%}" if exec_count > 0 else "-"
                table.add_row(
                    str(idx), name, desc, str(skill_type),
                    source, str(exec_count), success_str
                )
            
            self.console.print(table)
            self.console.print(f"[dim]Storage: {self.cerebellum.library._storage_path}[/dim]")
        except Exception as e:
            logger.warning(f"Error listing skills: {e}")

    async def _show_learning_progress(self):
        """Display learning progress report using Hippocampus analytics.

        Shows:
        - Per-skill mastery level, confidence, success rate
        - Competency scores
        - Practice recommendations
        - Consolidation status
        """
        if not self.hippocampus or not self.user_id:
            self.console.print("[yellow]Learning system not available.[/yellow]")
            return

        profile = self.hippocampus.get_user_profile(self.user_id)
        if not profile or not profile.skill_progress:
            self.console.print("[yellow]📊 No learning data yet — try learning some skills first![/yellow]")
            return

        # ── Skill mastery table ──
        table = Table(title="📊 Learning Progress Report")
        table.add_column("#", style="dim", width=3)
        table.add_column("Skill", style="cyan")
        table.add_column("Mastery", style="yellow")
        table.add_column("Confidence", style="green", justify="right")
        table.add_column("Success Rate", style="magenta", justify="right")
        table.add_column("Executions", style="white", justify="right")

        mastery_emoji = {
            "novice": "🌱",
            "beginner": "🌿",
            "intermediate": "🌳",
            "advanced": "⭐",
            "expert": "🏆",
        }

        for idx, (skill_id, progress) in enumerate(profile.skill_progress.items(), 1):
            name = progress.skill_name
            level = progress.mastery_level
            emoji = mastery_emoji.get(level, "")
            conf = f"{progress.confidence:.0%}"
            rate = f"{progress.success_rate:.0%}" if progress.execution_count > 0 else "-"
            runs = str(progress.execution_count)
            table.add_row(str(idx), name, f"{emoji} {level}", conf, rate, runs)

        self.console.print(table)

        # ── Competency summary ──
        try:
            summary = self.hippocampus.get_user_competency_summary(self.user_id)
            if summary:
                avg_score = summary.get("average_competency", 0)
                total_skills = summary.get("total_skills", 0)
                mastered = summary.get("mastered_skills", 0)
                self.console.print(
                    f"\n[bold]Overall[/bold]: {total_skills} skills tracked, "
                    f"{mastered} mastered, "
                    f"avg competency: [green]{avg_score:.0%}[/green]"
                )
        except Exception as e:
            logger.debug(f"Competency summary error: {e}")

        # ── Practice recommendations ──
        try:
            recommendations = self.hippocampus.get_practice_recommendations(self.user_id, limit=3)
            if recommendations:
                self.console.print("\n[bold]💡 Suggested practice:[/bold]")
                for skill_id, skill_name, gap in recommendations:
                    self.console.print(f"  • [yellow]{skill_name}[/yellow] (improvement potential: {gap:.0%})")
        except Exception as e:
            logger.debug(f"Recommendations error: {e}")

        # ── Consolidation status ──
        try:
            review_schedule = self.hippocampus.get_review_schedule(self.user_id)
            if review_schedule:
                self.console.print("\n[bold]📅 Skills due for review:[/bold]")
                for skill_id, review_time in review_schedule[:5]:
                    progress = profile.skill_progress.get(skill_id)
                    name = progress.skill_name if progress else skill_id
                    self.console.print(f"  • [cyan]{name}[/cyan] — due {review_time.strftime('%Y-%m-%d')}")
        except Exception as e:
            logger.debug(f"Review schedule error: {e}")

    def _print_user_stats(self):
        """Display user information (includes persisted history)."""
        if not self.user:
            self.console.print("[yellow]User profile not set.[/yellow]")
            return
        
        table = Table(title="👤 User Profile")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Name", self.user.name or "Unknown")
        table.add_row("User ID", self.user_id or "Not set")
        table.add_row("Status", "🎉 Old friend" if self._is_returning_user else "🆕 New user")
        table.add_row("Session Start", self.session_start.strftime("%Y-%m-%d %H:%M:%S"))
        
        # Add persisted stats
        persisted = self._find_profile_by_name(self.user.name) if self.user.name else None
        if persisted:
            table.add_row("First Seen", persisted.get("created_at", "Unknown")[:19])
            table.add_row("Last Seen", persisted.get("last_seen", "Unknown")[:19])
            table.add_row("Total Sessions", str(persisted.get("session_count", 1)))
            table.add_row("Total Interactions", str(persisted.get("total_interactions", 0)))
        
        if self.hippocampus and self.user_id:
            try:
                profile = self.hippocampus.get_user_profile(self.user_id)
                if profile:
                    skills_known = getattr(profile, 'skill_progress', {})
                    table.add_row("Skills Learned", str(len(skills_known) if skills_known else 0))
            except Exception as e:
                logger.debug(f"Error getting stats: {e}")
        
        self.console.print(table)

    # ── Session summary & conversation persistence ──────────────────

    async def _summarize_and_save_session(self):
        """Summarize the conversation via LLM and persist to user profile."""
        if not self.conversation_history or not self.user:
            return

        self.console.print("[dim]📝 Summarizing our conversation...[/dim]")

        summary = await self._generate_session_summary()
        if not summary:
            summary = self._fallback_summary()

        # Persist summary to user_profiles.json
        profiles = self._load_user_profiles()
        uid = self.user_id
        if uid and uid in profiles:
            entry = profiles[uid]
            if "conversation_summaries" not in entry:
                entry["conversation_summaries"] = []
            entry["conversation_summaries"].append({
                "date": self.session_start.strftime("%Y-%m-%d %H:%M"),
                "exchanges": len(self.conversation_history),
                "summary": summary,
            })
            # Keep only last 20 summaries to avoid unbounded growth
            entry["conversation_summaries"] = entry["conversation_summaries"][-20:]
            entry["last_seen"] = datetime.now().isoformat()
            self._save_user_profiles(profiles)
            logger.info(f"Saved session summary for {self.user.name} ({len(self.conversation_history)} exchanges)")

        self.console.print(f"[green]✓ Session memory saved.[/green]")

    async def _generate_session_summary(self) -> Optional[str]:
        """Use LLM to generate a concise summary of the conversation."""
        if not self.llm_client:
            return None

        # Build conversation text for the summarizer
        conv_lines = []
        for entry in self.conversation_history[-30:]:  # last 30 turns max
            conv_lines.append(f"User: {entry['user_input']}")
            resp = entry.get("response", "")
            # Strip markers for clarity
            for m in ["[ACTION_REQUIRED]", "[CODE_REQUIRED]", "[LIST_SKILLS]", "[USER_PROFILE]", "[CHAT]"]:
                resp = resp.replace(m, "")
            conv_lines.append(f"Assistant: {resp.strip()[:200]}")

        conversation_text = "\n".join(conv_lines)

        messages = [
            Message(role="system", content=(
                "You are a memory consolidation module for an embodied robot brain. "
                "Summarize the following conversation between a user and the robot brain into a concise paragraph (3-5 sentences). "
                "Include: topics discussed, skills learned or used, any user preferences or requests expressed, and key outcomes. "
                "Write in the same language the user used (Chinese or English). "
                "Be factual and brief."
            )),
            Message(role="user", content=f"Conversation with {self.user.name}:\n\n{conversation_text}"),
        ]

        try:
            response = await self.llm_client.call(
                messages=messages,
                temperature=0.3,
                max_tokens=512,
            )
            return response.content.strip() if response and response.content else None
        except Exception as e:
            logger.warning(f"Session summary generation failed: {e}")
            return None

    def _fallback_summary(self) -> str:
        """Generate a basic summary without LLM."""
        topics = []
        for entry in self.conversation_history:
            topics.append(entry["user_input"][:50])
        return f"Discussed: {'; '.join(topics[:10])}"

    def _get_past_summaries_for_prompt(self) -> str:
        """Retrieve past conversation summaries for the system prompt."""
        if not self.user or not self.user_id:
            return ""

        profiles = self._load_user_profiles()
        entry = profiles.get(self.user_id, {})
        summaries = entry.get("conversation_summaries", [])
        if not summaries:
            return ""

        lines = ["Previous conversation summaries with this user:"]
        for s in summaries[-5:]:  # last 5 sessions
            lines.append(f"- [{s.get('date', '?')}] ({s.get('exchanges', '?')} exchanges): {s.get('summary', 'N/A')}")
        return "\n".join(lines)

    def _print_goodbye(self):
        """Print goodbye message."""
        self.console.print("\nThank you for talking with me" + (f", {self.user.name}" if self.user else "") + "!")
        if self.user:
            self.console.print("\nI'll remember:")
            self.console.print("  • Your name and preferences")
            self.console.print("  • Skills we practiced together")
            self.console.print("  • Our conversation")
            self.console.print(f"\n  Session: {len(self.conversation_history)} exchanges")
        self.console.print("\n👋 Goodbye!\n")


async def start_embodied_brain(robot_body: Optional[RobotType] = None):
    """Main entry point for starting the embodied brain interface."""
    interface = EmbodiedBrainInterface(robot_body=robot_body)
    await interface.start()


if __name__ == "__main__":
    asyncio.run(start_embodied_brain(robot_body=RobotType.G1))
