"""Intent parser - Convert LLM responses into structured Intent objects."""

import json
import logging
from typing import List, Dict, Any, Optional

from openerb.core.types import Intent, TaskStatus

logger = logging.getLogger(__name__)


class IntentParser:
    """Parse LLM responses into structured Intent objects.
    
    Handles:
    - JSON response parsing
    - Intent object creation
    - Error recovery and fallback
    - Validation
    """

    def parse(self, response_text: str) -> List[Intent]:
        """Parse LLM response into Intent objects.

        Args:
            response_text: Raw text from LLM

        Returns:
            List of Intent objects

        Raises:
            RuntimeError: If parsing fails completely
        """
        logger.debug(f"Parsing LLM response: {response_text[:200]}...")

        # Try to extract JSON from response
        json_obj = self._extract_json(response_text)

        if not json_obj:
            logger.warning("No JSON found in response, using fallback parsing")
            return self._fallback_parse(response_text)

        # Parse intents from JSON
        intents = []
        intent_data_list = json_obj.get("intents", [])

        if not intent_data_list:
            logger.warning("No intents in JSON response")
            return []

        for intent_data in intent_data_list:
            try:
                intent = self._parse_single_intent(intent_data)
                if intent:
                    intents.append(intent)
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse intent: {e}, skipping")
                continue

        if not intents:
            logger.warning("No valid intents parsed, attempting fallback")
            return self._fallback_parse(response_text)

        logger.info(f"Successfully parsed {len(intents)} intents")
        return intents

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from text.

        Looks for JSON in common patterns:
        - {...}
        - ```json ... ```
        - json: {...}

        Args:
            text: Text potentially containing JSON

        Returns:
            Parsed JSON object or None
        """
        # Try direct JSON parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try markdown code block
        try:
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                if end > start:
                    json_text = text[start:end].strip()
                    return json.loads(json_text)
            elif "```" in text:
                start = text.find("```") + 3
                end = text.find("```", start)
                if end > start:
                    json_text = text[start:end].strip()
                    return json.loads(json_text)
        except (json.JSONDecodeError, ValueError):
            pass

        # Try to find {...} pattern
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_text = text[start:end]
                return json.loads(json_text)
        except (json.JSONDecodeError, ValueError):
            pass

        return None

    def _parse_single_intent(self, data: Dict[str, Any]) -> Optional[Intent]:
        """Parse a single intent from JSON data.

        Args:
            data: Intent data dictionary

        Returns:
            Intent object or None if invalid

        Raises:
            KeyError: If required fields are missing
            ValueError: If values are invalid
        """
        # Required fields
        action = data.get("action", "").strip()
        if not action:
            raise ValueError("Action is required")

        # Optional fields
        parameters = data.get("parameters", {})
        if not isinstance(parameters, dict):
            parameters = {}

        confidence = float(data.get("confidence", 0.5))
        if not 0 <= confidence <= 1:
            confidence = 0.5

        constraints = data.get("constraints", {})
        if not isinstance(constraints, dict):
            constraints = {}

        intent = Intent(
            raw_text=action,
            action=action,
            parameters=parameters,
            confidence=confidence,
            constraints=constraints,
        )

        logger.debug(f"Parsed intent: action={action}, confidence={confidence}")
        return intent

    def _fallback_parse(self, text: str) -> List[Intent]:
        """Fallback parsing when JSON extraction fails.

        Extracts intents from natural language patterns.

        Args:
            text: Raw response text

        Returns:
            List of Intent objects (may be empty)
        """
        intents = []

        # Look for common action patterns
        action_keywords = [
            "move", "walk", "grasp", "pick", "place", "rotate", "push", "pull",
            "jump", "sit", "stand", "look", "find", "follow", "learn", "execute"
        ]

        text_lower = text.lower()

        for action in action_keywords:
            if action in text_lower:
                intent = Intent(
                    raw_text=text,
                    action=action,
                    parameters={},
                    confidence=0.3,  # Lower confidence for fallback
                )
                intents.append(intent)
                logger.debug(f"Fallback: found action '{action}' in text")
                break  # Only one intent per fallback parse

        # If no action found, create generic intent
        if not intents:
            intent = Intent(
                raw_text=text,
                action="unknown",
                parameters={"raw_input": text},
                confidence=0.1,
            )
            intents.append(intent)
            logger.debug("Fallback: created unknown intent")

        return intents

    @staticmethod
    def validate_intent(intent: Intent) -> bool:
        """Validate an Intent object.

        Args:
            intent: Intent to validate

        Returns:
            True if valid

        Raises:
            ValueError: If invalid
        """
        if not intent.action:
            raise ValueError("Intent action cannot be empty")
        if not 0 <= intent.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        return True
