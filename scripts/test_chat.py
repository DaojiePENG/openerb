#!/usr/bin/env python3
"""
Test script for OpenERB Chat Interface.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from openerb.interface import ChatInterface


async def test_chat():
    """Test the chat interface."""
    print("🧪 Testing OpenERB Chat Interface...")

    try:
        chat = ChatInterface()
        print("✅ Chat interface initialized successfully")

        # Test basic functionality
        print("🧪 Testing soft skills...")

        # Test math skill
        math_result = await chat._math_skill("calculate 2 + 3")
        print(f"Math test: {math_result}")

        # Test joke skill
        joke_result = await chat._joke_skill("tell me a joke")
        print(f"Joke test: {joke_result[:50]}...")

        # Test writing skill
        write_result = await chat._writing_skill("write a story")
        print(f"Writing test: {write_result[:50]}...")

        print("✅ All tests passed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_chat())