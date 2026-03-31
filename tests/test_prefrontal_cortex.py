"""Unit tests for PrefrontalCortex module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from openerb.core.types import Intent, Subtask, UserProfile, RobotType, TaskStatus
from openerb.modules.prefrontal_cortex import (
    PrefrontalCortex,
    IntentParser,
    TaskDecomposer,
    ContextManager,
)
from openerb.llm.base import Message, LLMResponse


class TestIntentParser:
    """Test IntentParser."""

    def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        parser = IntentParser()
        response = """{
            "intents": [
                {
                    "action": "move",
                    "parameters": {"direction": "forward"},
                    "confidence": 0.9
                }
            ]
        }"""
        intents = parser.parse(response)

        assert len(intents) == 1
        assert intents[0].action == "move"
        assert intents[0].confidence == 0.9
        assert intents[0].parameters["direction"] == "forward"

    def test_parse_json_with_markdown(self):
        """Test parsing JSON in markdown code block."""
        parser = IntentParser()
        response = """Here's the analysis:
        ```json
        {
            "intents": [
                {"action": "grasp", "confidence": 0.8}
            ]
        }
        ```"""
        intents = parser.parse(response)

        assert len(intents) == 1
        assert intents[0].action == "grasp"

    def test_parse_fallback(self):
        """Test fallback parsing when JSON extraction fails."""
        parser = IntentParser()
        response = "The user wants to move the robot forward quickly"
        intents = parser.parse(response)

        assert len(intents) >= 1
        assert intents[0].action == "move"
        assert intents[0].confidence < 0.5  # Lower confidence for fallback

    def test_parse_fallback_unknown(self):
        """Test fallback when no action detected."""
        parser = IntentParser()
        response = "This is a random message about something"
        intents = parser.parse(response)

        assert len(intents) == 1
        assert intents[0].action == "unknown"
        assert intents[0].confidence <= 0.1

    def test_validate_intent_valid(self):
        """Test intent validation."""
        intent = Intent(
            raw_text="test",
            action="move",
            parameters={},
            confidence=0.8,
        )
        assert IntentParser.validate_intent(intent) is True

    def test_validate_intent_invalid_action(self):
        """Test validation fails with empty action."""
        intent = Intent(
            raw_text="test",
            action="",
            parameters={},
            confidence=0.8,
        )
        with pytest.raises(ValueError):
            IntentParser.validate_intent(intent)

    def test_validate_intent_invalid_confidence(self):
        """Test validation fails with invalid confidence."""
        intent = Intent(
            raw_text="test",
            action="move",
            parameters={},
            confidence=1.5,  # > 1
        )
        with pytest.raises(ValueError):
            IntentParser.validate_intent(intent)


class TestTaskDecomposer:
    """Test TaskDecomposer."""

    @pytest.mark.asyncio
    async def test_decompose_move(self):
        """Test decomposition of move action."""
        decomposer = TaskDecomposer()
        intent = Intent(
            raw_text="move forward",
            action="move",
            parameters={"direction": "forward"},
            confidence=0.9,
        )
        subtasks = await decomposer.decompose(intent)

        assert len(subtasks) >= 1
        assert subtasks[0].intent == intent
        assert all(hasattr(t, "task_id") for t in subtasks)
        assert all(hasattr(t, "priority") for t in subtasks)

    @pytest.mark.asyncio
    async def test_decompose_grasp(self):
        """Test decomposition of grasp action."""
        decomposer = TaskDecomposer()
        intent = Intent(
            raw_text="grasp the ball",
            action="grasp",
            parameters={"object": "ball"},
            confidence=0.8,
        )
        subtasks = await decomposer.decompose(intent)

        assert len(subtasks) >= 1
        # Should have main task + decomposed subtasks
        assert len(subtasks) > 1

    @pytest.mark.asyncio
    async def test_decompose_learn(self):
        """Test decomposition of learn action."""
        decomposer = TaskDecomposer()
        intent = Intent(
            raw_text="learn to walk",
            action="learn",
            parameters={},
            confidence=0.7,
        )
        subtasks = await decomposer.decompose(intent)

        assert len(subtasks) >= 1
        # Learn should decompose into multiple steps
        assert len(subtasks) > 1

    @pytest.mark.asyncio
    async def test_decompose_invalid_intent(self):
        """Test decomposition fails with None intent."""
        decomposer = TaskDecomposer()
        with pytest.raises(ValueError):
            await decomposer.decompose(None)

    def test_resolve_dependencies(self):
        """Test dependency resolution."""
        intent = Intent(
            raw_text="test",
            action="move",
            parameters={},
            confidence=0.8,
        )
        task1 = Subtask(intent=intent, task_id="1", dependencies=[])
        task2 = Subtask(intent=intent, task_id="2", dependencies=["1"])

        subtasks = TaskDecomposer.resolve_dependencies([task1, task2])
        assert len(subtasks) == 2
        assert subtasks[1].dependencies == ["1"]

    def test_resolve_circular_dependency(self):
        """Test circular dependency detection."""
        intent = Intent(
            raw_text="test",
            action="move",
            parameters={},
            confidence=0.8,
        )
        task1 = Subtask(intent=intent, task_id="1", dependencies=["2"])
        task2 = Subtask(intent=intent, task_id="2", dependencies=["1"])

        with pytest.raises(ValueError, match="Circular"):
            TaskDecomposer.resolve_dependencies([task1, task2])


class TestContextManager:
    """Test ContextManager."""

    def test_init(self):
        """Test initialization."""
        manager = ContextManager(max_turns=10)
        assert manager.max_turns == 10
        assert len(manager.turns) == 0

    def test_add_turn(self):
        """Test adding conversation turns."""
        from openerb.core.types import ConversationTurn

        manager = ContextManager(max_turns=5)
        turn = ConversationTurn(user_input="Hello")

        manager.add_turn(turn)
        assert len(manager.turns) == 1
        assert manager.turns[0] == turn

    def test_max_turns_bound(self):
        """Test max turns boundary."""
        from openerb.core.types import ConversationTurn

        manager = ContextManager(max_turns=3)

        for i in range(5):
            turn = ConversationTurn(user_input=f"Message {i}")
            manager.add_turn(turn)

        # Should only keep last 3
        assert len(manager.turns) == 3
        assert manager.turns[0].user_input == "Message 2"

    def test_get_history(self):
        """Test history retrieval."""
        from openerb.core.types import ConversationTurn

        manager = ContextManager()
        turns = [ConversationTurn(user_input=f"Turn {i}") for i in range(3)]

        for turn in turns:
            manager.add_turn(turn)

        history = manager.get_history()
        assert len(history) == 3

        last_2 = manager.get_history(last_n=2)
        assert len(last_2) == 2

    def test_set_current_user(self):
        """Test setting current user."""
        manager = ContextManager()
        user = UserProfile(name="Alice")

        manager.set_current_user(user)
        assert manager.context.current_user == user

    def test_clear_history(self):
        """Test clearing history."""
        from openerb.core.types import ConversationTurn

        manager = ContextManager()
        turn = ConversationTurn(user_input="test")
        manager.add_turn(turn)

        assert len(manager.turns) == 1
        manager.clear_history()
        assert len(manager.turns) == 0

    def test_export_json(self):
        """Test JSON export."""
        from openerb.core.types import ConversationTurn
        import json

        manager = ContextManager()
        turn = ConversationTurn(user_input="test")
        manager.add_turn(turn)

        exported = manager.export_history(format="json")
        data = json.loads(exported)

        assert "turns" in data
        assert "context" in data
        assert len(data["turns"]) == 1

    def test_export_text(self):
        """Test text export."""
        from openerb.core.types import ConversationTurn

        manager = ContextManager()
        turn = ConversationTurn(user_input="test input")
        manager.add_turn(turn)

        exported = manager.export_history(format="text")
        assert "test input" in exported
        assert "Turn 1" in exported


class TestPrefrontalCortex:
    """Test PrefrontalCortex."""

    def test_init_valid(self):
        """Test initialization with valid LLM client."""
        mock_llm = MagicMock()
        mock_llm.provider.model = "test-model"

        cortex = PrefrontalCortex(llm_client=mock_llm)
        assert cortex.llm_client == mock_llm
        assert cortex.max_conversation_history == 20

    def test_init_missing_client(self):
        """Test initialization fails without LLM client."""
        with pytest.raises(ValueError, match="LLM client"):
            PrefrontalCortex(llm_client=None)

    @pytest.mark.asyncio
    async def test_process_input_valid(self):
        """Test processing valid input."""
        mock_llm = MagicMock()
        mock_llm.provider.model = "test-model"

        mock_response = LLMResponse(
            content='{"intents": [{"action": "move", "confidence": 0.9}]}',
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
        )

        mock_llm.call = AsyncMock(return_value=mock_response)

        cortex = PrefrontalCortex(llm_client=mock_llm)

        with patch(
            "openerb.modules.prefrontal_cortex.intent_parser.IntentParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            intent = Intent(
                raw_text="move forward",
                action="move",
                parameters={},
                confidence=0.9,
            )
            mock_parser.parse.return_value = [intent]
            mock_parser_class.return_value = mock_parser

            with patch(
                "openerb.modules.prefrontal_cortex.task_decomposer.TaskDecomposer"
            ) as mock_decomposer_class:
                mock_decomposer = MagicMock()
                subtask = Subtask(intent=intent, task_id="1")
                mock_decomposer.decompose = AsyncMock(return_value=[subtask])
                mock_decomposer_class.return_value = mock_decomposer

                result = await cortex.process_input(text="move forward")

                assert result.intents is not None
                assert len(result.intents) == 1
                assert result.intents[0].action == "move"

    @pytest.mark.asyncio
    async def test_process_input_empty_text(self):
        """Test process_input fails with empty text."""
        mock_llm = MagicMock()
        mock_llm.provider.model = "test-model"

        cortex = PrefrontalCortex(llm_client=mock_llm)

        with pytest.raises(ValueError, match="Text input"):
            await cortex.process_input(text="")

    def test_get_context(self):
        """Test getting conversation context."""
        mock_llm = MagicMock()
        mock_llm.provider.model = "test-model"

        cortex = PrefrontalCortex(llm_client=mock_llm)
        context = cortex.get_context()

        assert context is not None
        assert context == cortex.conversation_context

    def test_clear_history(self):
        """Test clearing history."""
        mock_llm = MagicMock()
        mock_llm.provider.model = "test-model"

        cortex = PrefrontalCortex(llm_client=mock_llm)

        # Add a turn
        from openerb.core.types import ConversationTurn

        turn = ConversationTurn(user_input="test")
        cortex.conversation_turns.append(turn)

        assert len(cortex.conversation_turns) == 1

        cortex.clear_history()

        assert len(cortex.conversation_turns) == 0
