"""Learning Profile Manager - Manage user learning profiles and preferences."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from openerb.core.types import RobotType, Skill

logger = logging.getLogger(__name__)


@dataclass
class LearningPreferences:
    """User's learning preferences and settings."""
    learning_speed: str = "normal"  # "slow", "normal", "fast"
    focus_areas: List[str] = field(default_factory=list)  # e.g., ["manipulation", "movement"]
    preferred_complexity: str = "medium"  # "simple", "medium", "complex"
    retention_threshold: float = 0.7  # Min confidence to retain skill
    max_concurrent_skills: int = 5
    learning_style: str = "mixed"  # "theory", "practice", "mixed"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillProgress:
    """Progress tracking for a specific skill."""
    skill_id: str
    skill_name: str
    learned_at: datetime
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    success_rate: float = 0.0
    confidence: float = 0.0
    last_executed: Optional[datetime] = None
    last_success: Optional[datetime] = None
    mastery_level: str = "novice"  # "novice", "intermediate", "advanced", "expert"


@dataclass
class UserLearningProfile:
    """Complete learning profile for a user."""
    user_id: str
    user_name: str
    robot_type: RobotType
    preferences: LearningPreferences = field(default_factory=LearningPreferences)
    
    # Learning statistics
    total_skills_attempted: int = 0
    total_skills_mastered: int = 0
    total_execution_time: float = 0.0  # seconds
    
    # Skill tracking
    skill_progress: Dict[str, SkillProgress] = field(default_factory=dict)
    currently_learning: List[str] = field(default_factory=list)  # Skill IDs
    mastered_skills: List[str] = field(default_factory=list)
    failed_skills: List[str] = field(default_factory=list)
    
    # Timeline
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    last_learning_session: Optional[datetime] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)


class LearningProfileManager:
    """Manage user learning profiles and preferences."""
    
    def __init__(self):
        """Initialize profile manager."""
        self.profiles: Dict[str, UserLearningProfile] = {}
        logger.info("LearningProfileManager initialized")
    
    def create_profile(
        self,
        user_id: str,
        user_name: str,
        robot_type: RobotType,
        preferences: Optional[LearningPreferences] = None
    ) -> UserLearningProfile:
        """Create a new learning profile.
        
        Args:
            user_id: Unique user ID
            user_name: User's name
            robot_type: Target robot type
            preferences: Optional learning preferences
        
        Returns:
            Created UserLearningProfile
        """
        if user_id in self.profiles:
            logger.warning(f"Profile already exists for user {user_id}")
            return self.profiles[user_id]
        
        profile = UserLearningProfile(
            user_id=user_id,
            user_name=user_name,
            robot_type=robot_type,
            preferences=preferences or LearningPreferences()
        )
        
        self.profiles[user_id] = profile
        logger.info(f"Created learning profile for {user_name} ({user_id})")
        
        return profile
    
    def get_profile(self, user_id: str) -> Optional[UserLearningProfile]:
        """Get user's learning profile.
        
        Args:
            user_id: User ID
        
        Returns:
            UserLearningProfile or None
        """
        return self.profiles.get(user_id)
    
    def update_preferences(
        self,
        user_id: str,
        preferences: LearningPreferences
    ) -> bool:
        """Update user's learning preferences.
        
        Args:
            user_id: User ID
            preferences: New preferences
        
        Returns:
            True if updated
        """
        profile = self.get_profile(user_id)
        if not profile:
            logger.warning(f"Profile not found for {user_id}")
            return False
        
        profile.preferences = preferences
        profile.last_updated = datetime.now()
        logger.info(f"Updated preferences for {user_id}")
        
        return True
    
    def add_skill_progress(
        self,
        user_id: str,
        skill: Skill
    ) -> Optional[SkillProgress]:
        """Add a skill to user's learning progress.
        
        Args:
            user_id: User ID
            skill: Skill to track
        
        Returns:
            SkillProgress or None
        """
        profile = self.get_profile(user_id)
        if not profile:
            logger.warning(f"Profile not found for {user_id}")
            return None
        
        progress = SkillProgress(
            skill_id=skill.skill_id,
            skill_name=skill.name,
            learned_at=datetime.now()
        )
        
        profile.skill_progress[skill.skill_id] = progress
        profile.currently_learning.append(skill.skill_id)
        profile.total_skills_attempted += 1
        profile.last_updated = datetime.now()
        
        logger.info(f"Added skill {skill.name} to {user_id}'s learning profile")
        
        return progress
    
    def update_skill_progress(
        self,
        user_id: str,
        skill_id: str,
        success: bool,
        execution_time: float = 0.0
    ) -> Optional[SkillProgress]:
        """Update progress for a skill execution.
        
        Args:
            user_id: User ID
            skill_id: Skill ID
            success: Whether execution was successful
            execution_time: Execution duration in seconds
        
        Returns:
            Updated SkillProgress or None
        """
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        progress = profile.skill_progress.get(skill_id)
        if not progress:
            logger.warning(f"No progress found for skill {skill_id}")
            return None
        
        progress.execution_count += 1
        progress.last_executed = datetime.now()
        profile.total_execution_time += execution_time
        
        if success:
            progress.success_count += 1
            progress.last_success = datetime.now()
        else:
            progress.failure_count += 1
        
        # Update success rate
        progress.success_rate = (
            progress.success_count / progress.execution_count
            if progress.execution_count > 0 else 0.0
        )
        
        # Update confidence (exponential moving average)
        if success:
            progress.confidence = min(0.99, progress.confidence + 0.1)
        else:
            progress.confidence = max(0.0, progress.confidence - 0.05)
        
        profile.last_updated = datetime.now()
        profile.last_learning_session = datetime.now()
        
        return progress
    
    def promote_to_mastered(self, user_id: str, skill_id: str) -> bool:
        """Mark skill as mastered.
        
        Args:
            user_id: User ID
            skill_id: Skill ID
        
        Returns:
            True if promoted
        """
        profile = self.get_profile(user_id)
        if not profile:
            return False
        
        progress = profile.skill_progress.get(skill_id)
        if not progress:
            return False
        
        if skill_id in profile.currently_learning:
            profile.currently_learning.remove(skill_id)
        
        if skill_id not in profile.mastered_skills:
            profile.mastered_skills.append(skill_id)
        
        progress.mastery_level = "expert"
        progress.confidence = 0.9
        profile.total_skills_mastered += 1
        profile.last_updated = datetime.now()
        
        logger.info(f"Skill {skill_id} mastered by {user_id}")
        
        return True
    
    def mark_skill_failed(self, user_id: str, skill_id: str) -> bool:
        """Mark skill as failed (too many failures).
        
        Args:
            user_id: User ID
            skill_id: Skill ID
        
        Returns:
            True if marked
        """
        profile = self.get_profile(user_id)
        if not profile:
            return False
        
        progress = profile.skill_progress.get(skill_id)
        if not progress:
            return False
        
        if skill_id in profile.currently_learning:
            profile.currently_learning.remove(skill_id)
        
        if skill_id not in profile.failed_skills:
            profile.failed_skills.append(skill_id)
        
        progress.mastery_level = "novice"
        progress.confidence = 0.0
        profile.last_updated = datetime.now()
        
        logger.info(f"Skill {skill_id} marked as failed for {user_id}")
        
        return True
    
    def get_skill_progress(self, user_id: str, skill_id: str) -> Optional[SkillProgress]:
        """Get progress for specific skill.
        
        Args:
            user_id: User ID
            skill_id: Skill ID
        
        Returns:
            SkillProgress or None
        """
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        return profile.skill_progress.get(skill_id)
    
    def get_learning_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get learning summary for user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with learning summary or None
        """
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        return {
            "user_id": user_id,
            "user_name": profile.user_name,
            "robot_type": profile.robot_type.value,
            "total_attempted": profile.total_skills_attempted,
            "total_mastered": profile.total_skills_mastered,
            "mastery_rate": (
                profile.total_skills_mastered / profile.total_skills_attempted
                if profile.total_skills_attempted > 0 else 0.0
            ),
            "currently_learning": len(profile.currently_learning),
            "failed_skills": len(profile.failed_skills),
            "total_execution_time": profile.total_execution_time,
            "learning_preferences": {
                "speed": profile.preferences.learning_speed,
                "complexity": profile.preferences.preferred_complexity,
                "style": profile.preferences.learning_style
            },
            "last_learning_session": profile.last_learning_session,
            "created_at": profile.created_at
        }
    
    def get_user_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with detailed stats or None
        """
        profile = self.get_profile(user_id)
        if not profile:
            return None
        
        # Calculate avg success rate across all skills
        avg_success_rate = 0.0
        if profile.skill_progress:
            avg_success_rate = sum(
                p.success_rate for p in profile.skill_progress.values()
            ) / len(profile.skill_progress)
        
        # Calculate avg confidence
        avg_confidence = 0.0
        if profile.skill_progress:
            avg_confidence = sum(
                p.confidence for p in profile.skill_progress.values()
            ) / len(profile.skill_progress)
        
        return {
            "user_id": user_id,
            "total_skills_tracked": len(profile.skill_progress),
            "mastered_skills": len(profile.mastered_skills),
            "currently_learning": len(profile.currently_learning),
            "failed_skills": len(profile.failed_skills),
            "average_success_rate": avg_success_rate,
            "average_confidence": avg_confidence,
            "total_executions": sum(
                p.execution_count for p in profile.skill_progress.values()
            ),
            "total_successes": sum(
                p.success_count for p in profile.skill_progress.values()
            ),
            "learning_speed": profile.preferences.learning_speed,
            "days_learning": (
                (datetime.now() - profile.created_at).days
                if profile.created_at else 0
            )
        }
    
    def list_profiles(self) -> List[UserLearningProfile]:
        """Get all user profiles.
        
        Returns:
            List of UserLearningProfile
        """
        return list(self.profiles.values())
