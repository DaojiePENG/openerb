#!/usr/bin/env python3
"""
OpenERB Embodied Robot Brain - Main Chat Interface

This is the primary entry point for interacting with the embodied robot brain.
It provides a complete, integrated neural system for:
  • Understanding natural language requests
  • Learning new skills through conversation
  • Generating code to control the robot body
  • Persisting skills across sessions
  • Adapting to different robot hardware

The system works in stages:
  1. Soft Debugging (this interface) - Learn without physical robot
  2. Hardware Integration - Deploy brain to actual robot body
  3. Continuous Evolution - Robot learns in the real world
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from openerb.interface.embodied_brain_interface import start_embodied_brain
from openerb.core.types import RobotType


async def main():
    """Start the fully integrated embodied robot brain."""
    print("\n" + "="*70)
    print("🧠 OpenERB - Embodied Robot Brain")
    print("="*70)
    print("\n" + "="*70)
    print("COMPLETE NEURAL SYSTEM INTEGRATION")
    print("="*70)
    print("\n🎯 This interface provides:")
    print("   ✓ Full integration of all neural modules")
    print("   ✓ Natural language understanding (PrefrontalCortex)")
    print("   ✓ Autonomous code generation (MotorCortex)")
    print("   ✓ Skill persistence and learning (Hippocampus)")
    print("   ✓ Body awareness and adaptation (InsularCortex)")
    print("   ✓ Safety constraints (LimbicSystem)")
    print("   ✓ Multi-robot support (G1, Go2, Go1)")
    print("\n🚀 The brain can:")
    print("   • Learn new skills through conversation")
    print("   • Generate code for robot control")
    print("   • Remember and reuse learned skills")
    print("   • Adapt when deployed to different robot bodies")
    print("   • Make safe decisions and ask for clarification")
    print("\n💡 Type 'help' for commands or 'quit' to exit.")
    print("   Start with: 'learn how to [action]'\n")

    try:
        await start_embodied_brain(robot_body=RobotType.G1)
    except KeyboardInterrupt:
        pass


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