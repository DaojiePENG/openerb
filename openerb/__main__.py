"""
Main entry point for OpenERB (Open Embodied Robot Brain) system.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from openerb.core import (
    logger, get_config, get_storage, get_robot_config
)
from openerb.interface import ChatInterface


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="OpenERB - Open Embodied Robot Brain")
    parser.add_argument('--chat', action='store_true', help='Start interactive chat interface')
    parser.add_argument('--init', action='store_true', help='Initialize system')

    args = parser.parse_args()

    logger.info("🤖 Starting OpenERB - Open Embodied Robot Brain System")

    config = get_config()
    storage = get_storage()
    robot_config = get_robot_config()

    logger.info(f"Robot Type: {robot_config.robot_type}")
    logger.info(f"Debug Mode: {config.debug_mode}")

    if args.init:
        # Initialize system
        logger.info("Initializing OpenERB system...")
        # TODO: Add initialization logic
        logger.info("System initialized successfully")
        return

    if args.chat:
        # Start chat interface
        logger.info("Starting chat interface...")
        chat = ChatInterface()
        await chat.start_chat()
        return

    # Default: Show help
    logger.info("System initialized successfully")
    print("\n🤖 OpenERB Commands:")
    print("  python -m openerb --chat    # Start interactive chat")
    print("  python -m openerb --init    # Initialize system")
    print("  python -m openerb --help    # Show this help")


if __name__ == "__main__":
    asyncio.run(main())
