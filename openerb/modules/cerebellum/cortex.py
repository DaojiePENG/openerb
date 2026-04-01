"""Cerebellum - Main orchestrator for skill management system.

Coordinates all skill management components including library,
versioning, scoring, import/export, and garbage collection.
"""

import logging
from typing import Optional, List, Dict, Any
from openerb.core.types import Skill, SkillType, RobotType
from .skill_library import SkillLibrary
from .skill_version_manager import SkillVersionManager
from .skill_scorer import SkillScorer, ExecutionStatus
from .skill_exporter import SkillExporter
from .skill_trash_manager import SkillTrashManager

logger = logging.getLogger(__name__)


class Cerebellum:
    """Main API for skill management system.
    
    Orchestrates all cerebellum components:
    - SkillLibrary: Storage and retrieval
    - SkillVersionManager: Version control
    - SkillScorer: Performance tracking
    - SkillExporter: Import/export
    - SkillTrashManager: Garbage collection
    
    Example:
        >>> cerebellum = Cerebellum()
        >>> # Register a new skill
        >>> skill = Skill(name="grasp", ...)
        >>> skill_id = cerebellum.register_skill(skill, RobotType.G1)
        >>> # Search
        >>> results = cerebellum.search_skill("grasp")
        >>> # Record execution
        >>> cerebellum.record_execution(skill_id, ExecutionStatus.SUCCESS, 150)
        >>> # Get metrics
        >>> metrics = cerebellum.get_skill_metrics(skill_id)
        >>> # Export for sharing
        >>> json_str = cerebellum.export_skill(skill_id)
    """

    def __init__(self):
        """Initialize Cerebellum with all components."""
        self.library = SkillLibrary()
        self.version_manager = SkillVersionManager()
        self.scorer = SkillScorer()
        self.exporter = SkillExporter()
        self.trash_manager = SkillTrashManager()
        logger.debug("Initialized Cerebellum")

    # === Skill Library Operations ===

    def register_skill(
        self,
        skill: Skill,
        robot_body: Optional[RobotType] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Register a new skill.

        Args:
            skill: The skill to register
            robot_body: Target robot type
            description: Extended description
            tags: Search tags

        Returns:
            Skill ID
        """
        skill_id = self.library.register_skill(
            skill, robot_body, description, tags
        )

        # Create initial version - use only attributes that Skill has
        skill_data = {
            "name": skill.name,
            "description": skill.description,
            "code": skill.code,
            "skill_type": skill.skill_type.value,
            "dependencies": skill.dependencies,
            "tags": skill.tags,
            "supported_robots": [r.value for r in skill.supported_robots],
        }
        self.version_manager.create_version(
            skill_id,
            skill_data,
            "Initial registration"
        )

        return skill_id

    def search_skill(
        self,
        query: str,
        skill_type: Optional[SkillType] = None,
        robot_type: Optional[RobotType] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for skills.

        Args:
            query: Search query
            skill_type: Filter by type
            robot_type: Filter by robot
            tags: Filter by tags

        Returns:
            List of matching skills
        """
        return self.library.search_skill(
            query, skill_type, robot_type, tags
        )

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific skill.

        Args:
            skill_id: The skill ID

        Returns:
            Skill data if found
        """
        return self.library.get_skill(skill_id)

    def list_skills(
        self,
        robot_type: Optional[RobotType] = None,
        skill_type: Optional[SkillType] = None,
    ) -> List[Dict[str, Any]]:
        """List all skills with filtering.

        Args:
            robot_type: Filter by robot
            skill_type: Filter by type

        Returns:
            List of skills
        """
        return self.library.list_skills(robot_type, skill_type)

    def delete_skill(self, skill_id: str, reason: str = "User deletion") -> bool:
        """Delete a skill (soft delete to trash).

        Args:
            skill_id: Skill to delete
            reason: Deletion reason

        Returns:
            True if successful
        """
        skill = self.library.get_skill(skill_id)
        if not skill:
            return False

        # Move to trash
        self.trash_manager.move_to_trash(skill_id, skill, reason)
        return self.library.delete_skill(skill_id)

    # === Skill Version Operations ===

    def get_skill_versions(
        self,
        skill_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get version history for a skill.

        Args:
            skill_id: The skill ID
            limit: Max versions to return

        Returns:
            List of versions
        """
        return self.version_manager.list_versions(skill_id, limit)

    def update_skill_version(
        self,
        skill_id: str,
        new_data: Dict[str, Any],
        description: str,
    ) -> str:
        """Create new version of a skill.

        Args:
            skill_id: The skill ID
            new_data: Updated skill data
            description: Change description

        Returns:
            New version ID
        """
        # Update skill data
        self.library.update_skill(skill_id, new_data, "version_update")

        # Create new version
        version_id = self.version_manager.create_version(
            skill_id,
            new_data,
            description
        )
        return version_id

    def rollback_skill(
        self,
        skill_id: str,
        version_id: str,
        reason: str = "Rollback",
    ) -> bool:
        """Rollback a skill to previous version.

        Args:
            skill_id: The skill ID
            version_id: Target version
            reason: Rollback reason

        Returns:
            True if successful
        """
        return self.version_manager.rollback_to_version(
            skill_id, version_id, reason
        )

    def compare_skill_versions(
        self,
        skill_id: str,
        version1_id: str,
        version2_id: str,
    ) -> Dict[str, Any]:
        """Compare two versions of a skill.

        Args:
            skill_id: The skill ID
            version1_id: First version
            version2_id: Second version

        Returns:
            Difference report
        """
        return self.version_manager.compare_versions(
            version1_id, version2_id, skill_id
        )

    # === Skill Performance Operations ===

    def record_execution(
        self,
        skill_id: str,
        status: ExecutionStatus,
        duration_ms: int,
        parameters: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> str:
        """Record skill execution.

        Args:
            skill_id: The skill executed
            status: Execution status
            duration_ms: Execution time
            parameters: Execution parameters
            result: Execution result
            error_message: Error if any

        Returns:
            Execution ID
        """
        return self.scorer.record_execution(
            skill_id, status, duration_ms, parameters, result, error_message
        )

    def get_skill_metrics(self, skill_id: str) -> Dict[str, Any]:
        """Get performance metrics for a skill.

        Args:
            skill_id: The skill ID

        Returns:
            Performance metrics
        """
        return self.scorer.get_skill_metrics(skill_id)

    def rank_skills(
        self,
        limit: Optional[int] = None,
        metric: str = "competency_score",
    ) -> List[Dict[str, Any]]:
        """Rank skills by performance.

        Args:
            limit: Number to return
            metric: Ranking metric

        Returns:
            Ranked skills
        """
        return self.scorer.rank_skills(limit, metric)

    def get_execution_history(
        self,
        skill_id: str,
        last_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get execution history for a skill.

        Args:
            skill_id: The skill ID
            last_n: Last N executions

        Returns:
            Execution history
        """
        return self.scorer.get_execution_history(skill_id, last_n)

    # === Skill Import/Export Operations ===

    def export_skill(
        self,
        skill_id: str,
        format: str = "json",
        include_metadata: bool = True,
    ) -> str:
        """Export a skill.

        Args:
            skill_id: Skill to export
            format: Export format (json, yaml)
            include_metadata: Include metadata

        Returns:
            Exported skill string
        """
        skill = self.library.get_skill(skill_id)
        if not skill:
            return ""

        return self.exporter.export_skill(
            skill,
            skill.get("name", skill_id),
            format,
            include_metadata
        )

    def export_skill_to_file(
        self,
        skill_id: str,
        file_path: str,
        format: str = "json",
    ) -> bool:
        """Export skill to file.

        Args:
            skill_id: Skill to export
            file_path: Output file path
            format: Export format

        Returns:
            True if successful
        """
        skill = self.library.get_skill(skill_id)
        if not skill:
            return False

        return self.exporter.export_skill_to_file(
            skill,
            skill.get("name", skill_id),
            file_path,
            format
        )

    def import_skill(
        self,
        content: str,
        robot_body: Optional[RobotType] = None,
        format: str = "json",
    ) -> Optional[str]:
        """Import a skill from content.

        Args:
            content: Skill content (JSON/YAML)
            robot_body: Target robot
            format: Content format

        Returns:
            Skill ID if successful
        """
        skill_data = self.exporter.import_skill(content, format)
        if not skill_data:
            return None

        # Create skill object
        supported_robots = []
        if robot_body:
            supported_robots = [robot_body]
        
        skill = Skill(
            name=skill_data.get("name", "imported_skill"),
            description=f"Imported skill: {skill_data.get('name', 'unknown')}",
            code=skill_data.get("code", ""),
            skill_type=SkillType.HYBRID,
            supported_robots=supported_robots,
            tags=skill_data.get("tags", []),
        )

        return self.register_skill(
            skill,
            robot_body,
            description=f"Imported: {skill.name}"
        )

    def import_skill_from_file(
        self,
        file_path: str,
        robot_body: Optional[RobotType] = None,
        format: Optional[str] = None,
    ) -> Optional[str]:
        """Import skill from file.

        Args:
            file_path: File path
            robot_body: Target robot
            format: File format (auto-detect if None)

        Returns:
            Skill ID if successful
        """
        import os
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        from pathlib import Path
        content = Path(file_path).read_text()
        return self.import_skill(content, robot_body, format or "json")

    # === Trash/Garbage Collection Operations ===

    def restore_skill(self, skill_id: str) -> bool:
        """Restore a deleted skill from trash.

        Args:
            skill_id: Skill to restore

        Returns:
            True if successful
        """
        skill_data = self.trash_manager.restore(skill_id)
        if not skill_data:
            return False

        # Restore in library
        return self.library.update_skill(
            skill_id,
            skill_data,
            "restore_from_trash"
        )

    def get_trash(self) -> List[Dict[str, Any]]:
        """List deleted skills in trash.

        Returns:
            List of trashed skills
        """
        return self.trash_manager.list_trash()

    def empty_trash(
        self,
        days_old: int = 30,
        permanent: bool = True,
    ) -> int:
        """Empty trash.

        Args:
            days_old: Delete items older than N days
            permanent: Permanently delete if True

        Returns:
            Number of items deleted
        """
        return self.trash_manager.empty_trash(days_old, permanent)

    # === Statistics & Analytics ===

    def get_library_stats(self) -> Dict[str, Any]:
        """Get overall library statistics.

        Returns:
            Library stats
        """
        return self.library.get_library_stats()

    def get_trash_stats(self) -> Dict[str, Any]:
        """Get trash statistics.

        Returns:
            Trash stats
        """
        return self.trash_manager.get_trash_stats()

    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics.

        Returns:
            System-wide stats
        """
        return {
            "library": self.get_library_stats(),
            "trash": self.get_trash_stats(),
            "top_skills": self.rank_skills(limit=5),
        }
