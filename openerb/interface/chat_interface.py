"""
Chat Interface for OpenERB - Interactive conversation with the embodied robot brain.
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
from rich.columns import Columns
from rich.table import Table

from openerb.core.types import Intent, UserProfile, RobotType
from openerb.modules.prefrontal_cortex import PrefrontalCortex
from openerb.modules.hippocampus import Hippocampus
from openerb.modules.cerebellum import Cerebellum
from openerb.modules.system_integration import IntegrationEngine
from openerb.llm.config import LLMConfig
from openerb.core import get_config, logger


class ChatInterface:
    """Interactive chat interface for OpenERB system."""

    def __init__(self):
        self.console = Console()
        self.user_profile = UserProfile(
            user_id="chat_user",
            name="Human",
            preferences={}
        )

        # Initialize core modules
        try:
            llm_client = LLMConfig.create_client()
        except Exception as e:
            logger.warning(f"Failed to initialize LLM client: {e}, using mock mode")
            llm_client = None
        
        self.prefrontal_cortex = PrefrontalCortex(llm_client=llm_client) if llm_client else None
        self.hippocampus = Hippocampus()
        self.cerebellum = Cerebellum()
        self.integration_engine = IntegrationEngine(
            cerebellum=self.cerebellum,
            hippocampus=self.hippocampus
        )

        # Chat history
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_start_time = datetime.now()

        # Soft skills registry
        self.soft_skills = {
            "math": self._math_skill,
            "joke": self._joke_skill,
            "write": self._writing_skill,
            "explain": self._explanation_skill,
            "remember": self._memory_skill,
            "learn": self._learning_skill,
        }

    async def start_chat(self):
        """Start the interactive chat session."""
        self._show_welcome()

        try:
            while True:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self._show_goodbye()
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'history':
                    self._show_history()
                    continue
                elif user_input.lower() == 'stats':
                    self._show_stats()
                    continue
                elif user_input.lower().startswith('skill '):
                    await self._handle_skill_command(user_input[6:])
                    continue

                # Process user message
                await self._process_message(user_input)

        except KeyboardInterrupt:
            self._show_goodbye()
        except Exception as e:
            logger.error(f"Chat error: {e}")
            self.console.print(f"[red]Error: {e}[/red]")

    def _show_welcome(self):
        """Display welcome message."""
        welcome_text = Text("🤖 Welcome to OpenERB Chat Interface!", style="bold magenta")
        welcome_panel = Panel(
            "[green]I'm your embodied robot brain assistant![/green]\n\n"
            "[yellow]Available commands:[/yellow]\n"
            "• Type any message for conversation\n"
            "• 'help' - Show available commands\n"
            "• 'history' - View conversation history\n"
            "• 'stats' - Show learning statistics\n"
            "• 'skill [name]' - Demonstrate soft skills\n"
            "• 'quit' - Exit chat\n\n"
            "[blue]Try asking me to:[/blue]\n"
            "• Do math calculations\n"
            "• Tell jokes\n"
            "• Write something\n"
            "• Remember information\n"
            "• Learn new skills",
            title=welcome_text,
            border_style="blue"
        )
        self.console.print(welcome_panel)

    def _show_help(self):
        """Show help information."""
        help_table = Table(title="Available Commands")
        help_table.add_column("Command", style="cyan", no_wrap=True)
        help_table.add_column("Description", style="white")

        help_table.add_row("help", "Show this help message")
        help_table.add_row("history", "View conversation history")
        help_table.add_row("stats", "Show learning statistics")
        help_table.add_row("skill [name]", "Demonstrate soft skills")
        help_table.add_row("quit/exit", "Exit the chat interface")

        help_table.add_row("", "")
        help_table.add_row("Soft Skills Available:", "")
        help_table.add_row("math", "Mathematical calculations")
        help_table.add_row("joke", "Tell jokes and humor")
        help_table.add_row("write", "Writing and composition")
        help_table.add_row("explain", "Explanations and teaching")
        help_table.add_row("remember", "Memory and recall")
        help_table.add_row("learn", "Learning new information")

        self.console.print(help_table)

    def _show_history(self):
        """Show conversation history."""
        if not self.conversation_history:
            self.console.print("[yellow]No conversation history yet.[/yellow]")
            return

        history_table = Table(title="Conversation History")
        history_table.add_column("Time", style="dim", width=12)
        history_table.add_column("User", style="cyan", width=50)
        history_table.add_column("Robot", style="green", width=50)

        for entry in self.conversation_history[-10:]:  # Show last 10 entries
            time_str = entry['timestamp'].strftime("%H:%M:%S")
            user_msg = entry['user_message'][:47] + "..." if len(entry['user_message']) > 47 else entry['user_message']
            robot_msg = entry['robot_response'][:47] + "..." if len(entry['robot_response']) > 47 else entry['robot_response']

            history_table.add_row(time_str, user_msg, robot_msg)

        self.console.print(history_table)

    def _show_stats(self):
        """Show learning statistics."""
        try:
            stats = self.hippocampus.get_system_status()
            learning_summary = self.hippocampus.get_learning_summary("chat_user")

            stats_panel = Panel(
                f"[bold]Session Duration:[/bold] {datetime.now() - self.session_start_time}\n"
                f"[bold]Total Interactions:[/bold] {len(self.conversation_history)}\n"
                f"[bold]Skills Learned:[/bold] {learning_summary.get('total_skills_attempted', 0)}\n"
                f"[bold]Skills Mastered:[/bold] {learning_summary.get('total_skills_mastered', 0)}\n"
                f"[bold]Memory Items:[/bold] {stats.get('memory_items', 0)}",
                title="Learning Statistics",
                border_style="yellow"
            )
            self.console.print(stats_panel)
        except Exception as e:
            self.console.print(f"[red]Could not retrieve stats: {e}[/red]")

    def _show_goodbye(self):
        """Display goodbye message."""
        goodbye_panel = Panel(
            "[green]Thank you for chatting with me![/green]\n\n"
            f"[yellow]Session Summary:[/yellow]\n"
            f"• Duration: {datetime.now() - self.session_start_time}\n"
            f"• Interactions: {len(self.conversation_history)}\n\n"
            "[blue]Remember: I'm learning and growing with every conversation![/blue]",
            title="Goodbye! 👋",
            border_style="green"
        )
        self.console.print(goodbye_panel)

    async def _process_message(self, user_message: str):
        """Process user message and generate response."""
        # Show thinking indicator
        with self.console.status("[bold green]Thinking...", spinner="dots"):
            try:
                # Process through prefrontal cortex if available
                result = None
                if self.prefrontal_cortex:
                    result = await self.prefrontal_cortex.process_input(
                        text=user_message,
                        user=self.user_profile
                    )

                # Generate response based on intent
                response = await self._generate_response(user_message, result)

                # Record in hippocampus for learning
                await self._record_interaction(user_message, response, result)

                # Store in conversation history
                self.conversation_history.append({
                    'timestamp': datetime.now(),
                    'user_message': user_message,
                    'robot_response': response,
                    'intent': result.intents[0] if result and result.intents else None
                })

            except Exception as e:
                logger.error(f"Message processing error: {e}")
                response = f"I encountered an error processing your message: {e}"

        # Display response
        response_panel = Panel(
            response,
            title="[bold green]OpenERB[/bold green]",
            border_style="green"
        )
        self.console.print(response_panel)

    async def _generate_response(self, user_message: str, prefrontal_result=None) -> str:
        """Generate appropriate response based on user input."""
        # Check for soft skill requests
        for skill_name, skill_func in self.soft_skills.items():
            if skill_name in user_message.lower():
                return await skill_func(user_message)

        # Use integration engine for complex intents if result available
        if prefrontal_result and prefrontal_result.intents:
            intent = prefrontal_result.intents[0]
            try:
                result = await self.integration_engine.execute_intent(
                    intent, self.user_profile, RobotType.G1
                )
                return f"I processed your intent '{intent.action}'. Result: {result.get('status', 'completed')}"
            except Exception as e:
                logger.warning(f"Integration engine error: {e}")

        # Default conversational response
        return await self._generate_conversational_response(user_message)

    async def _generate_conversational_response(self, user_message: str) -> str:
        """Generate conversational response using LLM."""
        try:
            # Use prefrontal cortex for conversational response if available
            if self.prefrontal_cortex:
                response = await self.prefrontal_cortex.process_input(
                    text=f"Respond conversationally to: {user_message}",
                    user=self.user_profile
                )

                if response.intents and response.intents[0].action == "converse":
                    return "I'm here to chat and learn with you! What would you like to talk about?"

                return "I understand you're saying something interesting. I'm still learning how to respond naturally!"
            else:
                # Fallback without LLM
                return f"You said: '{user_message}'. That's interesting! I'm ready to learn from our conversation."

        except Exception as e:
            return f"I heard: '{user_message}'. I'm working on becoming a better conversationalist!"

    async def _record_interaction(self, user_message: str, response: str, prefrontal_result=None):
        """Record interaction for learning."""
        try:
            # Create a simple skill for conversation
            skill = {
                'name': 'conversation',
                'code': f'# Conversation: {user_message} -> {response}',
                'description': 'Learning conversational patterns'
            }

            # Record in hippocampus
            await self.hippocampus.record_skill_execution(
                user_id="chat_user",
                skill=skill,
                success=True,
                duration=1.0
            )
        except Exception as e:
            logger.debug(f"Recording interaction failed: {e}")

    async def _handle_skill_command(self, skill_name: str):
        """Handle skill demonstration command."""
        if skill_name in self.soft_skills:
            skill_func = self.soft_skills[skill_name]
            response = await skill_func(f"Show me {skill_name}")
            skill_panel = Panel(
                response,
                title=f"[bold blue]Skill: {skill_name.title()}[/bold blue]",
                border_style="blue"
            )
            self.console.print(skill_panel)
        else:
            available_skills = ", ".join(self.soft_skills.keys())
            self.console.print(f"[red]Unknown skill '{skill_name}'. Available: {available_skills}[/red]")

    # Soft Skills Implementation

    async def _math_skill(self, user_message: str) -> str:
        """Mathematical calculations skill."""
        try:
            # Simple math evaluation (in controlled environment)
            if "calculate" in user_message.lower() or "solve" in user_message.lower():
                # Extract math expression (very basic)
                import re
                math_match = re.search(r'(\d+(?:\s*[\+\-\*\/]\s*\d+)+)', user_message)
                if math_match:
                    expression = math_match.group(1).replace(' ', '')
                    result = eval(expression, {"__builtins__": {}})
                    return f"The result of {expression} is {result}"
                else:
                    return "I can help with basic math! Try: 'calculate 2 + 3 * 4'"
            else:
                return "I can do mathematical calculations! Ask me to 'calculate' something."
        except Exception as e:
            return f"Math error: {e}. Try simpler expressions!"

    async def _joke_skill(self, user_message: str) -> str:
        """Tell jokes skill."""
        jokes = [
            "Why did the robot go on a diet? Because it had too many bytes!",
            "What do you call a robot that always takes the longest path? Roko!",
            "Why was the math book sad? Because it had too many problems!",
            "What did the computer say to the robot? 'You byte!'",
            "Why did the AI go to school? To improve its learning algorithm!"
        ]

        import random
        joke = random.choice(jokes)
        return f"🤖 Here's a joke: {joke}"

    async def _writing_skill(self, user_message: str) -> str:
        """Writing and composition skill."""
        if "story" in user_message.lower():
            return "Once upon a time, there was a curious robot who loved learning from humans. Every conversation made it smarter and more helpful. The end! 📖"
        elif "poem" in user_message.lower():
            return "Roses are red,\nViolets are blue,\nI'm learning from you,\nAnd growing too! 📝"
        else:
            return "I can write stories, poems, or documents! Try asking for a 'story' or 'poem'."

    async def _explanation_skill(self, user_message: str) -> str:
        """Explanation and teaching skill."""
        topics = {
            "robot": "A robot is a machine that can perform tasks automatically. I'm an embodied robot brain that can learn and interact!",
            "ai": "AI stands for Artificial Intelligence. It's technology that allows machines to learn and make decisions.",
            "learning": "Learning is how I improve! Every conversation helps me understand better and remember new information.",
            "brain": "My 'brain' is made of different modules: prefrontal cortex for thinking, hippocampus for memory, cerebellum for skills!"
        }

        for topic, explanation in topics.items():
            if topic in user_message.lower():
                return explanation

        return "I can explain concepts! Try asking about: robot, AI, learning, or brain."

    async def _memory_skill(self, user_message: str) -> str:
        """Memory and recall skill."""
        if "remember" in user_message.lower():
            # Store something in memory
            memory_item = user_message.replace("remember", "").strip()
            if memory_item:
                try:
                    # Use hippocampus to store
                    await self.hippocampus.record_skill_execution(
                        user_id="chat_user",
                        skill={'name': 'memory', 'description': f'Remembered: {memory_item}'},
                        success=True,
                        duration=0.1
                    )
                    return f"✅ I'll remember: '{memory_item}'"
                except Exception as e:
                    return f"I tried to remember that, but encountered: {e}"
            else:
                return "What would you like me to remember?"
        else:
            return "I can remember things for you! Say 'remember [something]' and I'll store it."

    async def _learning_skill(self, user_message: str) -> str:
        """Learning new information skill."""
        if "teach" in user_message.lower() or "learn" in user_message.lower():
            return "I'm always learning! Every conversation helps me understand humans better. What would you like to teach me?"
        else:
            return "Learning is my favorite activity! I learn from every interaction. What new thing shall we explore together?"