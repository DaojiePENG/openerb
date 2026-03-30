"""
Main entry point for OpenERB (Open Embodied Robot Brain) system.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from openerb.core import (
    logger, get_config, get_storage, get_robot_config
)


async def main():
    """Main entry point."""
    logger.info("🤖 Starting OpenERB - Open Embodied Robot Brain System")
    
    config = get_config()
    storage = get_storage()
    robot_config = get_robot_config()
    
    logger.info(f"Robot Type: {robot_config.robot_type}")
    logger.info(f"Debug Mode: {config.debug_mode}")
    
    # TODO: Initialize modules and start conversation agent
    logger.info("System initialized successfully")
    
    # Placeholder for main loop
    logger.info("Ready for conversation input...")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
