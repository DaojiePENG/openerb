"""Skill Version Manager - Version control for skills.

Manages versioning of skills to track evolution, support rollbacks,
and maintain a full history of changes.
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SkillVersion:
    """Represents a single version of a skill."""

    version_id: str
    skill_id: str
    version_number: int
    skill_data: Dict[str, Any]
    created_at: datetime
    created_by: str
    description: str
    parent_version_id: Optional[str] = None


class SkillVersionManager:
    """Manage versioning and history for skills.
    
    Provides:
    - Version creation and tagging
    - Full history tracking with parent relationships
    - Diff calculation between versions
    - Rollback capability
    - Version comparison and analysis
    
    Example:
        >>> manager = SkillVersionManager()
        >>> skill_id = "grasp_skill_123"
        >>> v1 = manager.create_version(skill_id, skill_data, "Initial version")
        >>> # Update skill...
        >>> v2 = manager.create_version(skill_id, new_data, "Improved grasp force")
        >>> diff = manager.compare_versions(v1, v2)
        >>> # Rollback if needed
        >>> manager.rollback_to_version(skill_id, v1)
    """

    def __init__(self):
        """Initialize version manager."""
        self.versions: Dict[str, List[SkillVersion]] = {}  # skill_id -> versions
        self.version_counter: Dict[str, int] = {}  # skill_id -> latest version
        logger.debug("Initialized SkillVersionManager")

    def create_version(
        self,
        skill_id: str,
        skill_data: Dict[str, Any],
        description: str,
        created_by: str = "system",
    ) -> str:
        """Create a new version of a skill.

        Args:
            skill_id: The skill being versioned
            skill_data: Current state of the skill
            description: Description of changes in this version
            created_by: User/system creating the version

        Returns:
            Version ID
        """
        import uuid

        # Get next version number
        if skill_id not in self.version_counter:
            self.version_counter[skill_id] = 0
        
        self.version_counter[skill_id] += 1
        version_number = self.version_counter[skill_id]

        # Get parent version if exists
        parent_id = None
        if skill_id in self.versions and self.versions[skill_id]:
            parent_id = self.versions[skill_id][-1].version_id

        # Create version object
        version_id = str(uuid.uuid4())[:12]
        version = SkillVersion(
            version_id=version_id,
            skill_id=skill_id,
            version_number=version_number,
            skill_data=skill_data.copy(),
            created_at=datetime.now(),
            created_by=created_by,
            description=description,
            parent_version_id=parent_id,
        )

        # Store version
        if skill_id not in self.versions:
            self.versions[skill_id] = []
        self.versions[skill_id].append(version)

        logger.info(
            f"Created version {version_number} for skill {skill_id}: {description}"
        )
        return version_id

    def get_version(self, skill_id: str, version_id: str) -> Optional[SkillVersion]:
        """Get a specific version.

        Args:
            skill_id: The skill ID
            version_id: The version ID

        Returns:
            SkillVersion if found, None otherwise
        """
        if skill_id not in self.versions:
            return None

        for version in self.versions[skill_id]:
            if version.version_id == version_id:
                return version
        return None

    def get_latest_version(self, skill_id: str) -> Optional[SkillVersion]:
        """Get the latest version of a skill.

        Args:
            skill_id: The skill ID

        Returns:
            Latest SkillVersion if exists
        """
        if skill_id not in self.versions or not self.versions[skill_id]:
            return None
        return self.versions[skill_id][-1]

    def list_versions(
        self,
        skill_id: str,
        limit: Optional[int] = None,
    ) -> List[SkillVersion]:
        """List all versions of a skill.

        Args:
            skill_id: The skill ID
            limit: Maximum number of versions to return

        Returns:
            List of versions (newest first)
        """
        if skill_id not in self.versions:
            return []

        versions = self.versions[skill_id]
        if limit:
            versions = versions[-limit:]
        return list(reversed(versions))  # Newest first

    def rollback_to_version(
        self,
        skill_id: str,
        version_id: str,
        reason: str = "Manual rollback",
    ) -> bool:
        """Rollback to a previous version.

        Args:
            skill_id: The skill ID
            version_id: The target version ID
            reason: Reason for rollback

        Returns:
            True if rollback successful
        """
        source_version = self.get_version(skill_id, version_id)
        if not source_version:
            logger.error(f"Cannot rollback: version not found {version_id}")
            return False

        # Create new version with reverted data
        self.create_version(
            skill_id,
            source_version.skill_data,
            f"Rollback to v{source_version.version_number}: {reason}",
            created_by="system",
        )

        logger.info(
            f"Rolled back skill {skill_id} to version {source_version.version_number}"
        )
        return True

    def compare_versions(
        self,
        version1_id: str,
        version2_id: str,
        skill_id: str,
    ) -> Dict[str, Any]:
        """Compare two versions of a skill.

        Args:
            skill_id: The skill ID
            version1_id: First version to compare
            version2_id: Second version to compare

        Returns:
            Difference report
        """
        v1 = self.get_version(skill_id, version1_id)
        v2 = self.get_version(skill_id, version2_id)

        if not v1 or not v2:
            logger.error("Cannot compare: one or both versions not found")
            return {}

        return {
            "version1": {
                "id": v1.version_id,
                "number": v1.version_number,
                "description": v1.description,
                "created_at": v1.created_at.isoformat(),
            },
            "version2": {
                "id": v2.version_id,
                "number": v2.version_number,
                "description": v2.description,
                "created_at": v2.created_at.isoformat(),
            },
            "differences": self._calculate_diff(v1.skill_data, v2.skill_data),
        }

    def get_version_chain(self, skill_id: str) -> List[Dict[str, Any]]:
        """Get the parent-child chain of versions.

        Args:
            skill_id: The skill ID

        Returns:
            List of version chain with relationships
        """
        if skill_id not in self.versions:
            return []

        chain = []
        for version in self.versions[skill_id]:
            chain.append({
                "version_id": version.version_id,
                "version_number": version.version_number,
                "description": version.description,
                "creator": version.created_by,
                "created_at": version.created_at.isoformat(),
                "parent_version_id": version.parent_version_id,
            })
        return chain

    def get_version_stats(self, skill_id: str) -> Dict[str, Any]:
        """Get statistics about skill versions.

        Args:
            skill_id: The skill ID

        Returns:
            Version statistics
        """
        if skill_id not in self.versions:
            return {
                "total_versions": 0,
                "current_version": 0,
                "first_version_at": None,
                "last_updated_at": None,
            }

        versions = self.versions[skill_id]
        return {
            "total_versions": len(versions),
            "current_version": versions[-1].version_number,
            "first_version_at": versions[0].created_at.isoformat(),
            "last_updated_at": versions[-1].created_at.isoformat(),
            "unique_creators": len(set(v.created_by for v in versions)),
        }

    def _calculate_diff(
        self,
        data1: Dict[str, Any],
        data2: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate differences between two skill data objects.

        Args:
            data1: First skill data
            data2: Second skill data

        Returns:
            Difference report
        """
        added = {}
        removed = {}
        modified = {}

        # Check for added and modified keys
        for key, value2 in data2.items():
            if key not in data1:
                added[key] = value2
            elif data1[key] != value2:
                modified[key] = {
                    "from": data1[key],
                    "to": value2,
                }

        # Check for removed keys
        for key, value1 in data1.items():
            if key not in data2:
                removed[key] = value1

        return {
            "added": added,
            "removed": removed,
            "modified": modified,
        }
