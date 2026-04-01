"""Skill Trash Manager - Garbage collection for deleted skills.

Manages soft-deleted skills, restoration, and permanent deletion.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SkillTrashManager:
    """Manage deleted and trashed skills.
    
    Features:
    - Soft delete: Move skills to trash
    - Restore: Recover from trash
    - Permanent delete: Purge from trash
    - Retention: Auto-delete after N days
    
    Example:
        >>> manager = SkillTrashManager()
        >>> manager.move_to_trash("skill_123", "outdated")
        >>> trashed = manager.list_trash()
        >>> manager.restore("skill_123")
        >>> manager.empty_trash(days_old=30)
    """

    def __init__(self, retention_days: int = 30):
        """Initialize trash manager.

        Args:
            retention_days: Days to keep trashed skills before auto-delete
        """
        self.trash: Dict[str, Dict[str, Any]] = {}  # skill_id -> trash info
        self.retention_days = retention_days
        logger.debug(f"Initialized SkillTrashManager (retention={retention_days}d)")

    def move_to_trash(
        self,
        skill_id: str,
        skill_data: Dict[str, Any],
        reason: str,
    ) -> bool:
        """Move a skill to trash.

        Args:
            skill_id: The skill ID
            skill_data: The skill data
            reason: Reason for deletion

        Returns:
            True if successful
        """
        if skill_id in self.trash:
            logger.warning(f"Skill already in trash: {skill_id}")
            return False

        self.trash[skill_id] = {
            "skill_data": skill_data.copy(),
            "deleted_at": datetime.now().isoformat(),
            "deletion_reason": reason,
            "deleted_by": "system",
        }

        logger.info(f"Moved skill to trash: {skill_id} ({reason})")
        return True

    def restore(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Restore a skill from trash.

        Args:
            skill_id: The skill ID to restore

        Returns:
            Restored skill data if successful, None otherwise
        """
        if skill_id not in self.trash:
            logger.error(f"Skill not in trash: {skill_id}")
            return None

        trash_info = self.trash.pop(skill_id)
        skill_data = trash_info["skill_data"]

        # Update metadata
        metadata = skill_data.get("metadata", {})
        metadata["restored_at"] = datetime.now().isoformat()
        metadata["status"] = "active"
        skill_data["metadata"] = metadata

        logger.info(f"Restored skill from trash: {skill_id}")
        return skill_data

    def permanently_delete(self, skill_id: str) -> bool:
        """Permanently delete a skill from trash.

        Args:
            skill_id: The skill ID

        Returns:
            True if deleted
        """
        if skill_id not in self.trash:
            logger.error(f"Skill not in trash: {skill_id}")
            return False

        del self.trash[skill_id]
        logger.info(f"Permanently deleted skill: {skill_id}")
        return True

    def list_trash(self) -> List[Dict[str, Any]]:
        """List all trashed skills.

        Returns:
            List of trashed skills
        """
        result = []
        for skill_id, trash_info in self.trash.items():
            result.append({
                "skill_id": skill_id,
                "skill_name": trash_info["skill_data"].get("name"),
                "deleted_at": trash_info["deleted_at"],
                "reason": trash_info["deletion_reason"],
                "days_in_trash": self._days_in_trash(skill_id),
            })
        return result

    def empty_trash(
        self,
        days_old: int = 30,
        permanent: bool = True,
    ) -> int:
        """Empty trash of old items.

        Args:
            days_old: Only delete items older than N days
            permanent: If True, permanently delete; if False, just mark

        Returns:
            Number of items deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        to_delete = []

        for skill_id, trash_info in self.trash.items():
            deleted_at = datetime.fromisoformat(trash_info["deleted_at"])
            if deleted_at < cutoff_date:
                to_delete.append(skill_id)

        for skill_id in to_delete:
            if permanent:
                self.permanently_delete(skill_id)
            else:
                # Just mark as archived
                self.trash[skill_id]["archived_at"] = datetime.now().isoformat()

        logger.info(f"Emptied trash: {len(to_delete)} items deleted")
        return len(to_delete)

    def get_trash_stats(self) -> Dict[str, Any]:
        """Get trash statistics.

        Returns:
            Trash stats
        """
        if not self.trash:
            return {
                "total_items": 0,
                "total_size_bytes": 0,
                "oldest_item_days": 0,
            }

        # Calculate sizes
        total_size = 0
        oldest_date = None

        for trash_info in self.trash.values():
            skill_data = trash_info["skill_data"]
            total_size += len(str(skill_data))
            
            deleted_at = datetime.fromisoformat(trash_info["deleted_at"])
            if oldest_date is None or deleted_at < oldest_date:
                oldest_date = deleted_at

        oldest_days = (
            (datetime.now() - oldest_date).days
            if oldest_date else 0
        )

        return {
            "total_items": len(self.trash),
            "total_size_bytes": total_size,
            "oldest_item_days": oldest_days,
            "retention_days": self.retention_days,
            "items_to_auto_delete": sum(
                1 for info in self.trash.values()
                if self._days_in_trash_from_info(info) > self.retention_days
            ),
        }

    def can_restore(self, skill_id: str) -> bool:
        """Check if a skill can be restored.

        Args:
            skill_id: The skill ID

        Returns:
            True if can be restored
        """
        return skill_id in self.trash

    def _days_in_trash(self, skill_id: str) -> int:
        """Calculate days a skill has been in trash.

        Args:
            skill_id: The skill ID

        Returns:
            Number of days
        """
        if skill_id not in self.trash:
            return 0

        deleted_at = datetime.fromisoformat(
            self.trash[skill_id]["deleted_at"]
        )
        return (datetime.now() - deleted_at).days

    def _days_in_trash_from_info(self, trash_info: Dict[str, Any]) -> int:
        """Calculate days from trash info dict.

        Args:
            trash_info: Trash item info

        Returns:
            Number of days
        """
        deleted_at = datetime.fromisoformat(trash_info["deleted_at"])
        return (datetime.now() - deleted_at).days
