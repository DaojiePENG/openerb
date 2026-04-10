"""Skill Library - Core skill storage and retrieval system.

The Skill Library manages the persistent storage, organization, and
retrieval of robot skills. It provides searching, filtering, and
basic CRUD operations for skills.
"""

import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from openerb.core.types import Skill, SkillType, RobotType
from openerb.core.memory_optimizer import memory_optimizer

logger = logging.getLogger(__name__)


class SkillLibrary:
    """Manage skill storage, retrieval, and organization.
    
    This is the core component of the Cerebellum, providing:
    - Skill registration and CRUD operations
    - Advanced search and filtering
    - Integration with persistent storage
    - Metadata management
    
    Example:
        >>> library = SkillLibrary()
        >>> skill = Skill(
        ...     name="grasp_object",
        ...     skill_type=SkillType.PRIMITIVE,
        ...     required_capabilities=["grasp"],
        ... )
        >>> library.register_skill(skill, RobotType.G1)
        >>> results = library.search_skill("grasp", robot_type=RobotType.G1)
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize skill library with optional file persistence.
        
        Args:
            storage_path: Path to JSON file for persistent storage.
                          If None, skills are only kept in memory.
        """
        self.skills: Dict[str, Dict[str, Any]] = {}  # skill_id -> skill_data
        self._search_cache = {}  # Cache for search results
        self._skill_counter = 0  # Counter for generating IDs
        self._storage_path = storage_path
        
        # Load existing skills from disk
        if self._storage_path:
            self._load_from_disk()
        
        logger.debug(f"Initialized SkillLibrary ({len(self.skills)} skills loaded)")

    def register_skill(
        self,
        skill: Skill,
        robot_body: Optional[RobotType] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Register a new skill in the library.

        Args:
            skill: The Skill object to register
            robot_body: Target robot type (None = universal)
            description: Extended description
            tags: Search tags for categorization

        Returns:
            Skill ID after registration
        """
        import uuid
        
        # Generate skill ID
        skill_id = str(uuid.uuid4())[:12]
        
        # Create metadata
        metadata = {
            "created_at": datetime.now().isoformat(),
            "robot_type": robot_body.value if robot_body else "universal",
            "description": description or skill.description or "",
            "tags": tags or skill.tags or [],
            "execution_count": 0,
            "success_count": 0,
            "creation_source": "manual_registration",
        }

        # Store skill data - preserve all Skill attributes
        skill_data = {
            "id": skill_id,
            "name": skill.name,
            "description": skill.description,
            "code": skill.code,
            "skill_type": skill.skill_type.value,
            "dependencies": skill.dependencies,
            "tags": skill.tags,
            "supported_robots": [r.value for r in skill.supported_robots],
            "status": skill.status.value,
            "metadata": metadata,
        }

        self.skills[skill_id] = skill_data
        
        # Invalidate caches
        self._search_cache.clear()
        memory_optimizer.skill_cache.invalidate(skill_id)
        
        # Persist to disk
        self._save_to_disk()
        
        logger.info(f"Registered skill: {skill.name} (ID: {skill_id})")
        return skill_id

    def search_skill(
        self,
        query: str,
        skill_type: Optional[SkillType] = None,
        robot_type: Optional[RobotType] = None,
        tags: Optional[List[str]] = None,
        required_capabilities: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for skills matching criteria.

        Args:
            query: Search query (name, description, tags)
            skill_type: Filter by skill type
            robot_type: Filter by target robot
            tags: Filter by tags (any match)
            required_capabilities: Filter by required capabilities (ignored)

        Returns:
            List of matching skills with metadata
        """
        results = []

        # Meta-tags that should not participate in query matching
        _META_TAGS = {"auto_generated", "learned", "motor_cortex", "low", "medium", "high", "body_specific", "universal"}

        for skill_id, skill_data in self.skills.items():
            # Check query match (name, description, semantic tags only)
            query_lower = query.lower()
            name_match = query_lower in skill_data.get("name", "").lower()
            desc_match = query_lower in skill_data.get("description", "").lower()
            tags_list = skill_data.get("tags", [])
            # Only match against semantic tags, not meta-tags like "learned"/"auto_generated"
            semantic_tags = [t for t in tags_list if t.lower() not in _META_TAGS]
            tags_match = any(query_lower in tag.lower() for tag in semantic_tags)

            if not (name_match or desc_match or tags_match):
                continue

            # Check skill type filter
            if skill_type:
                if skill_data.get("skill_type") != skill_type.value:
                    continue

            # Check robot type filter
            if robot_type:
                robot_value = skill_data.get("robot_type", "universal")
                if robot_value != "universal" and robot_value != robot_type.value:
                    continue

            # Check tags filter
            if tags:
                if not any(tag in tags_list for tag in tags):
                    continue

            # Add to results with score
            result = {
                "id": skill_id,
                "name": skill_data.get("name"),
                "skill_type": skill_data.get("skill_type"),
                "robot_type": skill_data.get("robot_type"),
                "description": skill_data.get("description", ""),
                "tags": tags_list,
                "success_rate": self._calculate_success_rate(skill_data),
                "execution_count": skill_data.get("execution_count", 0),
                "created_at": skill_data.get("created_at"),
            }
            results.append(result)

        # Sort by relevance
        results.sort(
            key=lambda x: (
                query_lower not in x["name"].lower(),
                -x["execution_count"],
            )
        )

        logger.debug(f"Search '{query}' returned {len(results)} results")
        return results

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific skill by ID.

        Args:
            skill_id: The skill ID to retrieve

        Returns:
            Skill data if found, None otherwise
        """
        # Try cache first
        cached_skill = memory_optimizer.skill_cache.get(skill_id)
        if cached_skill:
            return cached_skill

        # Get from storage
        if skill_id in self.skills:
            skill_data = self.skills[skill_id]
            # Cache the result
            memory_optimizer.skill_cache.put(skill_id, skill_data)
            return skill_data

        logger.warning(f"Skill not found: {skill_id}")
        return None

    def update_skill(
        self,
        skill_id: str,
        skill_data: Dict[str, Any],
        update_source: str = "manual_update",
    ) -> bool:
        """Update an existing skill.

        Args:
            skill_id: The skill ID to update
            skill_data: Updated skill data
            update_source: Source of the update

        Returns:
            True if update successful, False otherwise
        """
        if skill_id not in self.skills:
            logger.error(f"Cannot update: skill not found {skill_id}")
            return False

        # Merge with existing data
        existing = self.skills[skill_id]
        updated = {**existing, **skill_data}
        
        # Update metadata
        metadata = updated.get("metadata", {})
        metadata["last_updated"] = datetime.now().isoformat()
        metadata["update_source"] = update_source
        updated["metadata"] = metadata

        self.skills[skill_id] = updated
        
        self._search_cache.clear()
        self._save_to_disk()
        logger.info(f"Updated skill: {skill_id}")
        return True

    def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill (soft delete to trash).

        Args:
            skill_id: The skill ID to delete

        Returns:
            True if deletion successful
        """
        skill = self.get_skill(skill_id)
        if not skill:
            logger.error(f"Cannot delete: skill not found {skill_id}")
            return False

        # Mark as deleted in metadata
        metadata = skill.get("metadata", {})
        metadata["deleted_at"] = datetime.now().isoformat()
        metadata["status"] = "trashed"
        
        self.update_skill(skill_id, {"metadata": metadata}, "soft_delete")
        
        self._search_cache.clear()
        self._save_to_disk()
        logger.info(f"Soft deleted skill: {skill_id}")
        return True

    def list_skills(
        self,
        robot_type: Optional[RobotType] = None,
        skill_type: Optional[SkillType] = None,
        exclude_deleted: bool = True,
    ) -> List[Dict[str, Any]]:
        """List all skills with optional filtering.

        Args:
            robot_type: Filter by robot type
            skill_type: Filter by skill type
            exclude_deleted: Exclude deleted skills

        Returns:
            List of skills matching criteria
        """
        results = []

        for skill_id, skill_data in self.skills.items():
            # Check deleted status
            if exclude_deleted:
                metadata = skill_data.get("metadata", {})
                if metadata.get("status") == "trashed":
                    continue

            # Check robot type filter
            if robot_type:
                robot_value = skill_data.get("robot_type", "universal")
                if robot_value != "universal" and robot_value != robot_type.value:
                    continue

            # Check skill type filter
            if skill_type:
                if skill_data.get("skill_type") != skill_type.value:
                    continue

            result = {
                "id": skill_id,
                "name": skill_data.get("name"),
                "description": skill_data.get("description"),
                "skill_type": skill_data.get("skill_type"),
                "robot_type": skill_data.get("robot_type"),
                "success_rate": self._calculate_success_rate(skill_data),
                "execution_count": skill_data.get("execution_count", 0),
            }
            results.append(result)

        return results

    def get_library_stats(self) -> Dict[str, Any]:
        """Get overall library statistics.

        Returns:
            Dictionary with library stats
        """
        total = len(self.skills)
        deleted = sum(
            1 for s in self.skills.values()
            if s.get("metadata", {}).get("status") == "trashed"
        )
        active = total - deleted

        # Group by skill type
        by_type = {}
        for skill in self.skills.values():
            skill_type = skill.get("skill_type", "unknown")
            by_type[skill_type] = by_type.get(skill_type, 0) + 1

        # Group by robot type
        by_robot = {}
        for skill in self.skills.values():
            robot_type = skill.get("robot_type", "universal")
            by_robot[robot_type] = by_robot.get(robot_type, 0) + 1

        # Calculate average success rate
        success_rates = [
            self._calculate_success_rate(s)
            for s in self.skills.values()
        ]
        avg_success = (
            sum(success_rates) / len(success_rates)
            if success_rates else 0.0
        )

        return {
            "total_skills": total,
            "active_skills": active,
            "deleted_skills": deleted,
            "by_skill_type": by_type,
            "by_robot_type": by_robot,
            "average_success_rate": avg_success,
        }

    def _load_all_skills(self) -> Dict[str, Dict[str, Any]]:
        """Load all skills from storage.

        Returns:
            Dictionary of skill_id -> skill_data
        """
        return self.skills.copy()

    def _calculate_success_rate(self, skill_data: Dict[str, Any]) -> float:
        """Calculate success rate from execution history.

        Args:
            skill_data: Skill data dictionary

        Returns:
            Success rate as float 0.0-1.0
        """
        metadata = skill_data.get("metadata", {})
        execution_count = metadata.get("execution_count", 0)
        success_count = metadata.get("success_count", 0)

        if execution_count == 0:
            return 1.0  # Unexecuted skills considered successful

        return success_count / execution_count

    # ========================================================================
    # Persistence
    # ========================================================================

    def _save_to_disk(self):
        """Persist all skills to JSON file."""
        if not self._storage_path:
            return
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            # Write to temp file first, then rename for atomicity
            tmp_path = self._storage_path.with_suffix('.tmp')
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(self.skills, f, indent=2, ensure_ascii=False)
            tmp_path.replace(self._storage_path)
            logger.debug(f"Persisted {len(self.skills)} skills to {self._storage_path}")
        except Exception as e:
            logger.error(f"Failed to persist skills: {e}")

    def _load_from_disk(self):
        """Load skills from JSON file."""
        if not self._storage_path or not self._storage_path.exists():
            return
        try:
            with open(self._storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.skills = data
                logger.info(f"Loaded {len(self.skills)} skills from {self._storage_path}")
            else:
                logger.warning(f"Invalid skill library format in {self._storage_path}")
        except Exception as e:
            logger.error(f"Failed to load skills from disk: {e}")
