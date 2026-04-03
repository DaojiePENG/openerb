#!/usr/bin/env python3
"""
Enhanced CLI chat interface for testing OpenERB capabilities without physical robot body.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openerb.interface import ChatInterface


async def main():
    """Start the interactive chat interface."""
    print("\n" + "="*60)
    print("🤖 OpenERB Chat Interface - Embodied Brain Learning Mode")
    print("="*60)
    print("\n💡 This interface lets you interact with the embodied robot brain")
    print("   without a physical body. You can:")
    print("   • Chat and have conversations")
    print("   • Teach it soft skills (math, jokes, writing, etc.)")
    print("   • Watch it learn and remember information")
    print("   • Explore its reasoning capabilities")
    print("\nType 'help' for available commands or 'quit' to exit.\n")

    chat = ChatInterface()
    await chat.start_chat()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)