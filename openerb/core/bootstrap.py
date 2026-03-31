"""
Bootstrap and initialization for the Self-Evolving Robot System.
"""

import os
import sys
import click
from pathlib import Path

from .config import get_config, set_config, SystemConfig, RobotConfig, get_storage_config
from .logger import logger, setup_logger
from .storage import get_storage


def setup_system(robot_type: str = "G1", debug: bool = False):
    """
    Setup the entire robot system.
    
    Args:
        robot_type: Type of robot (G1, Go2, etc.)
        debug: Enable debug mode
    """
    logger.info("=== Robot Self-Control System Bootstrap ===")
    logger.info(f"Setting up for robot type: {robot_type}")
    
    # Update config
    config = get_config()
    config.robot.robot_type = robot_type
    config.debug_mode = debug
    
    # Initialize storage
    storage = get_storage()
    logger.info(f"Storage initialized at: {storage.db_path}")
    
    # Create directories
    storage_config = get_storage_config()
    storage_config.ensure_directories()
    logger.info(f"Data directory: {storage_config.data_dir}")
    
    logger.info("Bootstrap complete!")


@click.group()
def cli():
    """Robot Self-Control System CLI."""
    pass


@cli.command()
@click.option("--robot-type", default="G1", help="Type of robot (G1, Go2, etc.)")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def init(robot_type: str, debug: bool):
    """Initialize the robot system."""
    setup_system(robot_type, debug)
    click.echo(f"✓ System initialized for {robot_type}")


@cli.command()
def status():
    """Show system status."""
    config = get_config()
    storage = get_storage()
    
    click.echo("\n=== System Status ===")
    click.echo(f"Robot Type: {config.robot.robot_type}")
    click.echo(f"Data Dir: {config.storage.data_dir}")
    click.echo(f"Database: {storage.db_path}")
    
    # List skills
    skills = storage.list_skills()
    click.echo(f"Skills: {len(skills)} total")
    
    for status_type in ["active", "deprecated", "retired"]:
        count = len(storage.list_skills(status_type))
        click.echo(f"  - {status_type}: {count}")


@cli.command()
def test():
    """Run system tests."""
    logger.info("Running system tests...")
    
    # Test storage
    from .types import Skill, SkillStatus, SkillType
    from datetime import datetime
    
    storage = get_storage()
    
    test_skill = Skill(
        name="test_skill",
        description="Test skill",
        code="print('Hello from test skill')",
        status=SkillStatus.DRAFT,
        skill_type=SkillType.UNIVERSAL,
        supported_robots=[],
        tags=["test"],
    )
    
    # Save and load
    if storage.save_skill(test_skill):
        logger.info("✓ Skill save successful")
    
    loaded = storage.load_skill(test_skill.skill_id)
    if loaded and loaded.name == "test_skill":
        logger.info("✓ Skill load successful")
    
    logger.info("Tests passed!")


if __name__ == "__main__":
    cli()
