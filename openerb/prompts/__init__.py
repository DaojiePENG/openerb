"""Prompt management for OpenERB LLM instances.

All system prompts are stored as .md files in this directory for easy editing.
Each file corresponds to a specific LLM usage point in the system.

Usage:
    from openerb.prompts import load_prompt

    prompt = load_prompt("chat_system")
    # Returns the raw markdown content of chat_system.md
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    """Load a prompt template from a .md file.

    Args:
        name: Prompt file name without the .md extension.
              e.g. "chat_system", "code_generator"

    Returns:
        The raw text content of the prompt file.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")
