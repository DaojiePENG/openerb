"""Conversation context manager - Maintain dialogue state."""

import logging
from typing import List, Optional
from datetime import datetime

from openerb.core.types import ConversationContext, ConversationTurn, UserProfile, RobotProfile

logger = logging.getLogger(__name__)


class ContextManager:
    """Manage conversation context and history.
    
    Handles:
    - Conversation history management
    - Context persistence and recovery
    - Turn-by-turn state tracking
    - Memory bounds
    """

    def __init__(self, max_turns: int = 20):
        """Initialize context manager.

        Args:
            max_turns: Maximum number of turns to keep in memory
        """
        self.max_turns = max_turns
        self.context = ConversationContext()
        self.turns: List[ConversationTurn] = []
        logger.info(f"Initialized ContextManager with max_turns={max_turns}")

    def add_turn(self, turn: ConversationTurn) -> None:
        """Add a conversation turn to history.

        Args:
            turn: ConversationTurn to add
        """
        self.turns.append(turn)
        logger.debug(f"Added conversation turn #{len(self.turns)}")

        # Maintain memory bounds
        if len(self.turns) > self.max_turns:
            removed = self.turns.pop(0)
            logger.debug(f"Removed oldest turn, keeping {len(self.turns)} turns")

    def get_history(self, last_n: Optional[int] = None) -> List[ConversationTurn]:
        """Get conversation history.

        Args:
            last_n: Return last N turns (None for all)

        Returns:
            List of ConversationTurn objects
        """
        if last_n is None:
            return self.turns.copy()

        if last_n <= 0:
            raise ValueError("last_n must be positive")

        return self.turns[-last_n:]

    def update_context(self, context: ConversationContext) -> None:
        """Update the conversation context.

        Args:
            context: New context to apply
        """
        self.context = context
        self.context.last_update = datetime.now()
        logger.debug("Conversation context updated")

    def get_context(self) -> ConversationContext:
        """Get current conversation context.

        Returns:
            Current ConversationContext
        """
        return self.context

    def set_current_user(self, user: Optional[UserProfile]) -> None:
        """Set current user in context.

        Args:
            user: User profile or None
        """
        self.context.current_user = user
        if user:
            logger.debug(f"Set current user: {user}")

    def set_current_robot(self, robot: Optional[RobotProfile]) -> None:
        """Set current robot in context.

        Args:
            robot: Robot profile or None
        """
        self.context.current_robot = robot
        if robot:
            logger.debug(f"Set current robot: {robot.robot_type}")

    def clear_history(self) -> None:
        """Clear all conversation history."""
        self.turns.clear()
        logger.info("Conversation history cleared")

    def clear_context(self) -> None:
        """Clear conversation context."""
        self.context = ConversationContext()
        logger.info("Conversation context cleared")

    def get_summary(self) -> str:
        """Get a summary of current conversation state.

        Returns:
            Summary string
        """
        lines = [
            f"Conversation Summary:",
            f"  Total turns: {len(self.turns)}",
            f"  Current user: {self.context.current_user}",
            f"  Current robot: {self.context.current_robot}",
            f"  Metadata: {len(self.context.metadata)} items",
        ]

        if self.turns:
            last_turn = self.turns[-1]
            lines.append(f"  Last turn at: {last_turn.timestamp}")

        return "\n".join(lines)

    def get_context_summary(self) -> str:
        """Get summary of context for LLM prompts.

        Returns:
            Context summary suitable for inclusion in prompts
        """
        if not self.context.current_user and not self.context.current_robot:
            return "No active context"

        lines = []
        if self.context.current_user:
            lines.append(f"User: {self.context.current_user}")
        if self.context.current_robot:
            lines.append(f"Robot: {self.context.current_robot.robot_type}")
        if self.context.current_task:
            lines.append(f"Task: {self.context.current_task.task_id}")

        return " | ".join(lines) if lines else "Empty context"

    def export_history(self, format: str = "json") -> str:
        """Export conversation history.

        Args:
            format: Export format ("json", "text")

        Returns:
            Formatted conversation history

        Raises:
            ValueError: If format is unsupported
        """
        if format == "json":
            import json
            from dataclasses import asdict

            try:
                data = {
                    "turns": [asdict(turn) for turn in self.turns],
                    "context": asdict(self.context),
                }
                return json.dumps(data, indent=2, default=str)
            except Exception as e:
                logger.error(f"Failed to export as JSON: {e}")
                raise

        elif format == "text":
            lines = ["Conversation History", "=" * 50]
            for i, turn in enumerate(self.turns, 1):
                lines.append(f"\nTurn {i}:")
                lines.append(f"  User: {turn.user_input}")
                if turn.robot_response:
                    lines.append(f"  Bot: {turn.robot_response}")
            return "\n".join(lines)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def __repr__(self) -> str:
        return f"ContextManager(turns={len(self.turns)}, max={self.max_turns})"
