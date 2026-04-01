"""Hippocampus - Long-term Memory Integration."""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from openerb.core.types import Skill, RobotType
from .learning_profile import LearningProfileManager, UserLearningProfile, SkillProgress
from .learning_history import LearningHistoryTracker, LearningEvent, LearningSession
from .consolidation_engine import ConsolidationEngine, ConsolidationRecord
from .competency_metrics import CompetencyMetrics, CompetencyScore

logger = logging.getLogger(__name__)


class Hippocampus:
    """Long-term memory system integrating learning management."""
    
    def __init__(self):
        """Initialize Hippocampus with all sub-components."""
        self.profile_manager = LearningProfileManager()
        self.history_tracker = LearningHistoryTracker()
        self.consolidation_engine = ConsolidationEngine()
        self.competency_metrics = CompetencyMetrics()
        
        logger.info("Hippocampus initialized with all memory systems")
    
    # ============================================================================
    # User Profile Management
    # ============================================================================
    
    def create_user_profile(
        self,
        user_id: str,
        user_name: str,
        robot_type: RobotType,
        learning_preferences: Optional[Dict] = None
    ) -> UserLearningProfile:
        """Create a new user learning profile.
        
        Args:
            user_id: User ID
            user_name: User name
            robot_type: Robot type
            learning_preferences: Optional preferences dict
        
        Returns:
            Created UserLearningProfile
        """
        profile = self.profile_manager.create_profile(
            user_id, user_name, robot_type, learning_preferences
        )
        
        # Start initial learning session
        self.history_tracker.start_session(user_id)
        
        logger.info(f"Created user profile for {user_name} ({robot_type})")
        
        return profile
    
    def get_user_profile(self, user_id: str) -> Optional[UserLearningProfile]:
        """Get user learning profile.
        
        Args:
            user_id: User ID
        
        Returns:
            UserLearningProfile or None
        """
        return self.profile_manager.get_profile(user_id)
    
    # ============================================================================
    # Skill Learning & Tracking
    # ============================================================================
    
    def start_learning(
        self,
        user_id: str,
        skill: Skill,
        focus_session: bool = True
    ) -> Tuple[SkillProgress, LearningSession]:
        """Start learning a new skill.
        
        Args:
            user_id: User ID
            skill: Skill to learn
            focus_session: Whether to create focused learning session
        
        Returns:
            Tuple of (SkillProgress, LearningSession)
        """
        # Add skill to learning profile
        progress = self.profile_manager.add_skill_progress(user_id, skill)
        
        # Start learning session
        session = self.history_tracker.start_session(
            user_id, focus_skill=skill.skill_id
        )
        
        logger.info(f"User {user_id} started learning {skill.name}")
        
        return progress, session
    
    def record_skill_execution(
        self,
        user_id: str,
        skill: Skill,
        success: bool,
        duration: float,
        result_details: Optional[str] = None,
        error_message: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Tuple[SkillProgress, LearningEvent]:
        """Record a skill execution.
        
        Args:
            user_id: User ID
            skill: Skill executed
            success: Whether execution was successful
            duration: Duration in seconds
            result_details: Optional result details
            error_message: Optional error message
            context: Optional execution context
        
        Returns:
            Tuple of (updated SkillProgress, LearningEvent)
        """
        # Get current profile for confidence tracking
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            logger.error(f"Profile not found for user {user_id}")
            return None, None
        
        skill_progress = profile.skill_progress.get(skill.skill_id)
        if not skill_progress:
            logger.error(f"No progress found for skill {skill.skill_id}")
            return None, None
        
        confidence_before = skill_progress.confidence
        
        # Update skill progress
        updated_progress = self.profile_manager.update_skill_progress(
            user_id, skill.skill_id, success, duration
        ) if hasattr(self.profile_manager, 'update_skill_progress') else None
        
        # Handle potential errors
        if updated_progress is None:
            logger.error(f"Failed to update skill progress for {skill.skill_id}")
            return None, None
        
        confidence_after = updated_progress.confidence
        
        # Record in history
        event = self.history_tracker.record_event(
            skill_id=skill.skill_id,
            skill_name=skill.name,
            user_id=user_id,
            duration=duration,
            success=success,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            execution_result=result_details,
            error_message=error_message,
            context=context or {}
        )
        
        # Check if skill should be promoted to mastered
        if updated_progress.success_rate >= 0.9 and updated_progress.execution_count >= 5:
            if updated_progress.mastery_level != "expert":
                self.profile_manager.promote_to_mastered(user_id, skill.skill_id)
                
                # Attempt consolidation
                consolidated, record = self.consolidation_engine.consolidate_skill(
                    skill.skill_id,
                    skill.name,
                    user_id,
                    confidence_after,
                    updated_progress.success_rate,
                    updated_progress.execution_count
                )
        
        logger.debug(
            f"Recorded execution for {skill.name}: "
            f"success={success}, confidence={confidence_after:.2f}"
        )
        
        return updated_progress, event
    
    def complete_learning_session(self, user_id: str) -> LearningSession:
        """Complete current learning session.
        
        Args:
            user_id: User ID
        
        Returns:
            Completed LearningSession
        """
        session = self.history_tracker.end_session()
        
        if session:
            logger.info(
                f"Completed learning session for {user_id} "
                f"with {len(session.events)} events"
            )
        
        return session
    
    # ============================================================================
    # Memory Consolidation & Spaced Repetition
    # ============================================================================
    
    def consolidate_learning(
        self,
        user_id: str,
        skill_id: str
    ) -> Tuple[bool, Optional[ConsolidationRecord]]:
        """Consolidate skill learning.
        
        Args:
            user_id: User ID
            skill_id: Skill ID
        
        Returns:
            Tuple of (consolidated, record)
        """
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            logger.error(f"Profile not found for user {user_id}")
            return False, None
        
        skill_progress = profile.skill_progress.get(skill_id)
        if not skill_progress:
            logger.error(f"No progress found for skill {skill_id}")
            return False, None
        
        # Consolidate
        consolidated, record = self.consolidation_engine.consolidate_skill(
            skill_id,
            skill_progress.skill_name,
            user_id,
            skill_progress.confidence,
            skill_progress.success_rate,
            skill_progress.execution_count
        )
        
        return consolidated, record
    
    def get_review_schedule(self, user_id: str) -> List[Tuple[str, datetime]]:
        """Get spaced repetition review schedule.
        
        Args:
            user_id: User ID
        
        Returns:
            List of (skill_id, review_time) tuples
        """
        return self.consolidation_engine.get_review_candidates(user_id, days_ahead=7)
    
    def record_skill_review(
        self,
        user_id: str,
        skill_id: str,
        quality: int
    ) -> Dict:
        """Record a skill review for spaced repetition.
        
        Args:
            user_id: User ID
            skill_id: Skill ID
            quality: Review quality (0-5)
        
        Returns:
            Dict with review results
        """
        schedule = self.consolidation_engine.record_review(
            skill_id, user_id, quality
        )
        
        # Also record as learning event
        if schedule:
            skill_progress = self.profile_manager.get_skill_progress(user_id, skill_id)
            if skill_progress:
                self.history_tracker.record_event(
                    skill_id=skill_id,
                    skill_name=skill_progress.skill_name,
                    user_id=user_id,
                    duration=0.0,
                    success=(quality >= 3),
                    confidence_before=skill_progress.confidence,
                    confidence_after=skill_progress.confidence,
                    notes=f"Spaced repetition review: quality {quality}/5"
                )
        
        return {
            "skill_id": skill_id,
            "next_review": schedule.next_review_time if schedule else None,
            "review_count": schedule.review_count if schedule else 0,
            "interval_days": schedule.interval_days if schedule else 0
        }
    
    # ============================================================================
    # Competency & Analytics
    # ============================================================================
    
    def calculate_competency(
        self,
        user_id: str,
        skill_id: str
    ) -> Optional[CompetencyScore]:
        """Calculate competency score for skill.
        
        Args:
            user_id: User ID
            skill_id: Skill ID
        
        Returns:
            CompetencyScore or None
        """
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            return None
        
        skill_progress = profile.skill_progress.get(skill_id)
        if not skill_progress:
            return None
        
        # Get learning history for this skill
        history = self.history_tracker.get_skill_history(
            skill_id, user_id=user_id, days=30
        )
        
        if not history:
            avg_duration = 0.0
        else:
            avg_duration = sum(e.duration for e in history) / len(history)
        
        # Get learning velocity from history
        learning_stats = self.history_tracker.get_learning_stats(user_id, days=7)
        
        score = self.competency_metrics.calculate_competency(
            skill_id=skill_id,
            skill_name=skill_progress.skill_name,
            user_id=user_id,
            success_rate=skill_progress.success_rate,
            average_duration=avg_duration,
            execution_count=skill_progress.execution_count,
            confidence=skill_progress.confidence,
            learning_velocity=(
                learning_stats.get("success_rate", 0.0) / 7.0
                if learning_stats else 0.0
            )
        )
        
        return score
    
    def get_user_competency_summary(self, user_id: str) -> Dict:
        """Get overall competency summary for user.
        
        Args:
            user_id: User ID
        
        Returns:
            Competency summary dict
        """
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            return {}
        
        # Calculate scores for all skills
        for skill_id in profile.skill_progress:
            self.calculate_competency(user_id, skill_id)
        
        # Get summary
        return self.competency_metrics.get_user_summary(user_id)
    
    def rank_skills(self, user_id: str, limit: int = 10) -> List[CompetencyScore]:
        """Rank user's skills by competency.
        
        Args:
            user_id: User ID
            limit: Maximum skills to return
        
        Returns:
            List of CompetencyScore sorted by competency
        """
        return self.competency_metrics.rank_skills(user_id, limit=limit)
    
    def get_practice_recommendations(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Tuple[str, str, float]]:
        """Get skill practice recommendations.
        
        Args:
            user_id: User ID
            limit: Maximum recommendations
        
        Returns:
            List of (skill_id, skill_name, improvement_gap) tuples
        """
        return self.competency_metrics.recommend_practice_skills(
            user_id, limit=limit
        )
    
    # ============================================================================
    # Learning Analytics & Insights
    # ============================================================================
    
    def get_learning_summary(self, user_id: str) -> Dict:
        """Get comprehensive learning summary.
        
        Args:
            user_id: User ID
        
        Returns:
            Learning summary dict
        """
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            return {}
        
        profile_summary = self.profile_manager.get_learning_summary(user_id)
        user_stats = self.profile_manager.get_user_stats(user_id)
        learning_stats = self.history_tracker.get_learning_stats(user_id, days=7)
        consolidation_status = self.consolidation_engine.get_consolidation_status(user_id)
        competency_summary = self.get_user_competency_summary(user_id)
        
        return {
            "user_id": user_id,
            "user_name": profile.user_name,
            "robot_type": profile.robot_type,
            "profile": profile_summary,
            "stats": user_stats,
            "recent_activity": learning_stats,
            "consolidation": consolidation_status,
            "competency": competency_summary
        }
    
    def get_skill_insights(
        self,
        user_id: str,
        skill_id: str
    ) -> Dict:
        """Get detailed insights for specific skill.
        
        Args:
            user_id: User ID
            skill_id: Skill ID
        
        Returns:
            Detailed skill insights
        """
        # Get skill progress
        skill_progress = self.profile_manager.get_skill_progress(user_id, skill_id)
        if not skill_progress:
            return {"error": "Skill not found"}
        
        # Get history
        history = self.history_tracker.get_skill_history(
            skill_id, user_id=user_id, days=30
        )
        
        # Get analytics
        analytics = self.history_tracker.get_skill_analytics(
            skill_id, user_id=user_id, days=30
        )
        
        # Get consolidation status
        consolidation = self.consolidation_engine.get_skill_consolidation(
            skill_id, user_id
        )
        
        # Get competency
        competency = self.competency_metrics.get_skill_strengths(
            skill_id, user_id
        )
        
        return {
            "skill_id": skill_id,
            "skill_name": skill_progress.skill_name,
            "progress": {
                "execution_count": skill_progress.execution_count,
                "success_rate": skill_progress.success_rate,
                "confidence": skill_progress.confidence,
                "mastery_level": skill_progress.mastery_level,
                "learned_at": skill_progress.learned_at.isoformat()
            },
            "history_count": len(history),
            "analytics": analytics,
            "consolidation": {
                "consolidated": consolidation is not None,
                "strength": consolidation.consolidation_strength if consolidation else None
            },
            "competency": competency
        }
    
    def get_consolidation_insights(self, user_id: str) -> Dict:
        """Get consolidation progress insights.
        
        Args:
            user_id: User ID
        
        Returns:
            Consolidation insights dict
        """
        return self.consolidation_engine.get_consolidation_insights(user_id)
    
    # ============================================================================
    # Data Export & Management
    # ============================================================================
    
    def export_learning_history(
        self,
        user_id: str,
        format: str = "json"
    ) -> str:
        """Export user's learning history.
        
        Args:
            user_id: User ID
            format: Export format ("json" or "csv")
        
        Returns:
            Exported history as string
        """
        return self.history_tracker.export_history(user_id, format=format)
    
    def cleanup_old_history(self, retention_days: int = 365) -> int:
        """Clean up old history records.
        
        Args:
            retention_days: Days to retain
        
        Returns:
            Number of records removed
        """
        return self.history_tracker.cleanup_old_history(retention_days)
    
    # ============================================================================
    # System Status & Monitoring
    # ============================================================================
    
    def get_system_status(self) -> Dict:
        """Get Hippocampus system status.
        
        Returns:
            System status dict
        """
        total_profiles = len(self.profile_manager.profiles)
        total_events = len(self.history_tracker.events)
        total_sessions = len(self.history_tracker.sessions)
        total_consolidations = len(self.consolidation_engine.consolidation_records)
        total_scores = len(self.competency_metrics.scores)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "profiles": total_profiles,
            "events": total_events,
            "sessions": total_sessions,
            "consolidations": total_consolidations,
            "competency_scores": total_scores,
            "components": {
                "profile_manager": "ready",
                "history_tracker": "ready",
                "consolidation_engine": "ready",
                "competency_metrics": "ready"
            }
        }
