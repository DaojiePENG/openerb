"""Prefrontal Cortex (前额叶皮层) - User interaction and intent understanding module.

The Prefrontal Cortex handles:
- Multi-modal user input (text + images)
- Intent recognition and classification
- Task planning and decomposition
- Conversation context management
- Natural language understanding

This is the entry point for all user interactions with the OpenERB system.
"""

import logging
from typing import Optional, List
from datetime import datetime

from openerb.core.types import Intent, Subtask, IntentResult, ConversationContext, ConversationTurn, UserProfile
from openerb.llm.client import LLMClient
from openerb.llm.base import Message

logger = logging.getLogger(__name__)


class PrefrontalCortex:
    """Prefrontal Cortex - User interaction and intent understanding.
    
    This module orchestrates the entire user interaction flow:
    1. Receive multi-modal input (text + image)
    2. Convert input to structured messages
    3. Call LLM for intent recognition
    4. Parse LLM response into Intent objects
    5. Decompose intent into subtasks
    6. Maintain and update conversation context
    7. Return structured result to caller
    
    The Prefrontal Cortex serves as the entry point for all downstream modules:
    - Insular Cortex uses Intent to identify robot
    - Cerebellum uses Intent to find relevant skills
    - Motor Cortex uses Intent + Subtasks to generate code
    - Limbic System uses Intent to assess safety
    
    Example:
        >>> from openerb.modules.prefrontal_cortex import PrefrontalCortex
        >>> from openerb.llm.config import LLMConfig
        >>> 
        >>> llm_client = LLMConfig.create_client()
        >>> cortex = PrefrontalCortex(llm_client=llm_client)
        >>> 
        >>> result = await cortex.process_input(
        ...     text="Make the robot walk forward",
        ...     image=None
        ... )
        >>> print(result.intents)
    """

    # System prompt for intent recognition
    SYSTEM_PROMPT = """You are an intelligent assistant for robotic control. 
Your task is to analyze user inputs and extract structured information about their intentions.

Analyze the user's request and return a JSON response with:
{
    "intents": [
        {
            "action": "primary action (move, grasp, learn, etc.)",
            "parameters": {"param1": "value1", ...},
            "confidence": 0.9 (0-1)
        }
    ],
    "subtasks": [
        {
            "task": "description",
            "priority": 1,
            "depends_on": []
        }
    ]
}

Be precise and concise in your response."""

    def __init__(
        self,
        llm_client: LLMClient,
        max_conversation_history: int = 20,
    ):
        """Initialize Prefrontal Cortex.

        Args:
            llm_client: Configured LLM client for intent recognition
            max_conversation_history: Maximum conversation turns to keep in memory

        Raises:
            ValueError: If llm_client is not provided
        """
        if not llm_client:
            raise ValueError("LLM client is required for Prefrontal Cortex")

        self.llm_client = llm_client
        self.max_conversation_history = max_conversation_history
        self.conversation_context = ConversationContext()
        self.conversation_turns: List[ConversationTurn] = []

        logger.info(
            f"Initialized PrefrontalCortex with model: {llm_client.provider.model}, "
            f"max_history: {max_conversation_history}"
        )

    async def process_input(
        self,
        text: str,
        image: Optional[bytes] = None,
        user: Optional[UserProfile] = None,
    ) -> IntentResult:
        """Process user input and return structured intent result.

        This is the main entry point for user interactions.

        Args:
            text: User's text input
            image: Optional image data (bytes)
            user: Optional user profile information

        Returns:
            IntentResult containing parsed intents, confidence, and updated context

        Raises:
            ValueError: If text is empty
            RuntimeError: If LLM call fails
        """
        logger.info(f"Processing user input: {text[:100]}...")

        # Validate input
        if not text or not isinstance(text, str):
            raise ValueError("Text input is required and must be a string")

        # Create conversation turn
        turn = ConversationTurn(user_input=text, user_image=image)

        try:
            # Convert input to message format
            messages = self._build_messages(text, image)

            # Call LLM for intent recognition
            llm_response = await self.llm_client.call(
                messages=messages,
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=1024,
            )

            logger.debug(f"LLM response: {llm_response.content}")

            # Parse response into Intent objects (implemented in intent_parser.py)
            # Temporarily: create placeholder
            from openerb.modules.prefrontal_cortex.intent_parser import IntentParser
            
            parser = IntentParser()
            intents = parser.parse(llm_response.content)

            # Decompose intents into subtasks (implemented in task_decomposer.py)
            from openerb.modules.prefrontal_cortex.task_decomposer import TaskDecomposer
            
            decomposer = TaskDecomposer()
            subtasks: List[Subtask] = []
            for intent in intents:
                subtasks.extend(await decomposer.decompose(intent))

            # Update conversation context
            self.conversation_context.current_user = user
            self.conversation_context.conversation_history.append(turn)
            turn.intents = intents
            
            # Keep conversation history within bounds
            if len(self.conversation_turns) >= self.max_conversation_history:
                self.conversation_turns.pop(0)
            self.conversation_turns.append(turn)

            logger.info(
                f"Intent processing complete: {len(intents)} intents, "
                f"{len(subtasks)} subtasks"
            )

            # Return structured result
            return IntentResult(
                intents=intents,
                confidence=min(i.confidence for i in intents) if intents else 0.0,
                context=self.conversation_context,
            )

        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            raise RuntimeError(f"Failed to process input: {e}") from e

    async def decompose_task(self, intent: Intent) -> List[Subtask]:
        """Decompose a single intent into subtasks.

        Args:
            intent: Intent to decompose

        Returns:
            List of subtasks

        Raises:
            ValueError: If intent is invalid
        """
        if not intent:
            raise ValueError("Intent is required")

        logger.debug(f"Decomposing intent: {intent.action}")

        from openerb.modules.prefrontal_cortex.task_decomposer import TaskDecomposer
        
        decomposer = TaskDecomposer()
        subtasks = await decomposer.decompose(intent)
        return subtasks

    def update_context(self, context: ConversationContext) -> None:
        """Update the conversation context.

        Args:
            context: New context to apply
        """
        self.conversation_context = context
        logger.debug("Conversation context updated")

    def get_context(self) -> ConversationContext:
        """Get current conversation context.

        Returns:
            Current ConversationContext
        """
        return self.conversation_context

    def clear_history(self) -> None:
        """Clear conversation history and context."""
        self.conversation_turns.clear()
        self.conversation_context = ConversationContext()
        logger.info("Conversation history cleared")

    def _build_messages(
        self,
        text: str,
        image: Optional[bytes] = None,
    ) -> List[Message]:
        """Build message list for LLM call.

        Args:
            text: User text
            image: Optional image bytes

        Returns:
            List of Message objects
        """
        messages = [
            Message(role="system", content=self.SYSTEM_PROMPT),
        ]

        # Add context from conversation history if available
        if self.conversation_turns:
            history_context = self._build_history_context()
            messages.append(
                Message(role="system", content=f"Previous conversation:\n{history_context}")
            )

        # Add user message
        messages.append(
            Message(
                role="user",
                content=text,
                image_base64=self._encode_image(image) if image else None,
            )
        )

        return messages

    def _build_history_context(self) -> str:
        """Build context string from conversation history.

        Returns:
            Formatted conversation history
        """
        if not self.conversation_turns:
            return ""

        # Keep last 3 turns for context
        recent_turns = self.conversation_turns[-3:]
        history_lines = []

        for turn in recent_turns:
            history_lines.append(f"User: {turn.user_input[:100]}")
            if turn.robot_response:
                history_lines.append(f"Assistant: {turn.robot_response[:100]}")

        return "\n".join(history_lines)

    @staticmethod
    def _encode_image(image_bytes: Optional[bytes]) -> Optional[str]:
        """Encode image bytes to base64.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Base64-encoded image string or None
        """
        if not image_bytes:
            return None

        import base64
        return base64.b64encode(image_bytes).decode("utf-8")

    def __repr__(self) -> str:
        return f"PrefrontalCortex(model={self.llm_client.provider.model})"
