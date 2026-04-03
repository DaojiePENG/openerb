#!/usr/bin/env python3
"""
Simplified test script for OpenERB Chat Interface debugging.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openerb.interface import ChatInterface


async def test_soft_skills():
    """Test soft skills implementation."""
    print("\n" + "="*50)
    print("🧪 Testing OpenERB Soft Skills")
    print("="*50)

    try:
        chat = ChatInterface()
        print("✅ Chat interface initialized\n")

        # Test each soft skill
        skills_tests = [
            ("math", "calculate 10 + 5 * 2"),
            ("joke", "tell me a joke"),
            ("write", "write a short story"),
            ("explain", "explain AI"),
            ("remember", "remember that I like Python"),
            ("learn", "teach me something new"),
        ]

        for skill_name, test_input in skills_tests:
            print(f"\n📌 Testing {skill_name.upper()} skill:")
            print(f"   Input: {test_input}")
            skill_func = chat.soft_skills.get(skill_name)
            if skill_func:
                result = await skill_func(test_input)
                print(f"   Output: {result[:100]}..." if len(result) > 100 else f"   Output: {result}")
                print(f"   ✅ {skill_name.upper()} test passed")
            else:
                print(f"   ❌ Skill {skill_name} not found")

        print("\n" + "="*50)
        print("✅ All soft skills tests completed!")
        print("="*50)

        # Summary
        print("\n📊 Skills Summary:")
        print(f"   Total skills: {len(chat.soft_skills)}")
        print(f"   Available: {', '.join(chat.soft_skills.keys())}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(test_soft_skills())