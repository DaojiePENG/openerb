"""Consolidation Engine - Skill consolidation and spaced repetition."""

import logging
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from openerb.core.types import Skill

logger = logging.getLogger(__name__)


@dataclass
class ConsolidationRecord:
    """Record of a skill consolidation event."""
    skill_id: str
    skill_name: str
    user_id: str
    consolidation_time: datetime
    confidence_gain: float
    memory_decay: float
    last_reviewed: Optional[datetime] = None
    review_count: int = 0
    consolidation_strength: float = 0.0  # 0-1, how well consolidated


@dataclass
class SpacedRepetitionSchedule:
    """Spaced repetition schedule for a skill."""
    skill_id: str
    user_id: str
    next_review_time: datetime
    review_count: int = 0
    interval_days: int = 1  # Days since last review
    ease_factor: float = 2.5  # SM-2 algorithm ease factor
    quality: List[int] = field(default_factory=list)  # Quality scores 0-5


class ConsolidationEngine:
    """Manage skill consolidation and spaced repetition."""
    
    # SM-2 algorithm constants
    MIN_EASE_FACTOR = 1.3
    MAX_EASE_FACTOR = 2.5
    
    def __init__(
        self,
        base_consolidation_strength: float = 0.7,
        memory_decay_rate: float = 0.95
    ):
        """Initialize consolidation engine.
        
        Args:
            base_consolidation_strength: Base strength threshold for consolidation (0-1)
            memory_decay_rate: Daily memory decay rate (0-1)
        """
        self.base_consolidation_strength = base_consolidation_strength
        self.memory_decay_rate = memory_decay_rate
        self.consolidation_records: Dict[str, ConsolidationRecord] = {}
        self.schedules: Dict[str, SpacedRepetitionSchedule] = {}
        logger.info(
            f"ConsolidationEngine initialized (strength: {base_consolidation_strength}, "
            f"decay_rate: {memory_decay_rate})"
        )
    
    def consolidate_skill(
        self,
        skill_id: str,
        skill_name: str,
        user_id: str,
        confidence: float,
        success_rate: float,
        execution_count: int
    ) -> Tuple[bool, ConsolidationRecord]:
        """Consolidate a skill into long-term memory.
        
        Args:
            skill_id: Skill ID
            skill_name: Skill name
            user_id: User ID
            confidence: Current confidence (0-1)
            success_rate: Success rate (0-1)
            execution_count: Number of executions
        
        Returns:
            Tuple of (consolidated, record)
        """
        # Calculate consolidation strength
        consolidation_strength = self._calculate_consolidation_strength(
            confidence, success_rate, execution_count
        )
        
        # Check if meets consolidation threshold
        consolidated = consolidation_strength >= self.base_consolidation_strength
        
        # Create consolidation record
        record = ConsolidationRecord(
            skill_id=skill_id,
            skill_name=skill_name,
            user_id=user_id,
            consolidation_time=datetime.now(),
            confidence_gain=confidence,
            memory_decay=1.0 - self.memory_decay_rate,
            consolidation_strength=consolidation_strength
        )
        
        record_key = f"{user_id}_{skill_id}"
        self.consolidation_records[record_key] = record
        
        if consolidated:
            # Initialize spaced repetition schedule
            self._initialize_schedule(skill_id, user_id)
            logger.info(
                f"Skill {skill_name} consolidated for {user_id} "
                f"(strength: {consolidation_strength:.2f})"
            )
        else:
            logger.debug(
                f"Skill {skill_name} not yet consolidated for {user_id} "
                f"(strength: {consolidation_strength:.2f})"
            )
        
        return consolidated, record
    
    def _calculate_consolidation_strength(
        self,
        confidence: float,
        success_rate: float,
        execution_count: int
    ) -> float:
        """Calculate consolidation strength.
        
        Args:
            confidence: Confidence level (0-1)
            success_rate: Success rate (0-1)
            execution_count: Number of executions
        
        Returns:
            Consolidation strength (0-1)
        """
        # Weight factors
        confidence_weight = 0.4
        success_weight = 0.3
        execution_weight = 0.3
        
        # Normalize execution count (logarithmic scale, cap at 10)
        execution_score = min(1.0, math.log(execution_count + 1) / math.log(11))
        
        # Calculate weighted strength
        strength = (
            confidence * confidence_weight +
            success_rate * success_weight +
            execution_score * execution_weight
        )
        
        return max(0.0, min(1.0, strength))
    
    def _initialize_schedule(self, skill_id: str, user_id: str) -> None:
        """Initialize spaced repetition schedule for skill.
        
        Args:
            skill_id: Skill ID
            user_id: User ID
        """
        schedule_key = f"{user_id}_{skill_id}"
        
        schedule = SpacedRepetitionSchedule(
            skill_id=skill_id,
            user_id=user_id,
            next_review_time=datetime.now() + timedelta(days=1),
            review_count=0,
            interval_days=1,
            ease_factor=2.5
        )
        
        self.schedules[schedule_key] = schedule
        logger.debug(f"Schedule initialized for {skill_id}")
    
    def get_review_candidates(
        self,
        user_id: str,
        days_ahead: int = 7
    ) -> List[Tuple[str, datetime]]:
        """Get skills due for review.
        
        Args:
            user_id: User ID
            days_ahead: Days to look ahead
        
        Returns:
            List of (skill_id, review_time) tuples
        """
        candidates = []
        now = datetime.now()
        future = now + timedelta(days=days_ahead)
        
        for schedule_key, schedule in self.schedules.items():
            if schedule.user_id != user_id:
                continue
            
            if now <= schedule.next_review_time <= future:
                candidates.append((schedule.skill_id, schedule.next_review_time))
        
        # Sort by review time
        candidates.sort(key=lambda x: x[1])
        
        return candidates
    
    def record_review(
        self,
        skill_id: str,
        user_id: str,
        quality: int
    ) -> SpacedRepetitionSchedule:
        """Record a review using SM-2 algorithm.
        
        Args:
            skill_id: Skill ID
            user_id: User ID
            quality: Quality of review (0-5)
        
        Returns:
            Updated SpacedRepetitionSchedule
        """
        schedule_key = f"{user_id}_{skill_id}"
        
        if schedule_key not in self.schedules:
            logger.warning(f"No schedule found for {schedule_key}")
            return None
        
        schedule = self.schedules[schedule_key]
        schedule.quality.append(quality)
        schedule.review_count += 1
        
        # SM-2 algorithm
        if quality < 3:
            # Failed review - reset
            schedule.interval_days = 1
            schedule.ease_factor = self.MIN_EASE_FACTOR
        else:
            # Successful review
            if schedule.review_count == 1:
                schedule.interval_days = 1
            elif schedule.review_count == 2:
                schedule.interval_days = 3
            else:
                schedule.interval_days = int(
                    schedule.interval_days * schedule.ease_factor
                )
            
            # Update ease factor
            schedule.ease_factor = max(
                self.MIN_EASE_FACTOR,
                schedule.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            )
        
        # Calculate next review time
        schedule.next_review_time = datetime.now() + timedelta(days=schedule.interval_days)
        
        # Update consolidation record
        record_key = f"{user_id}_{skill_id}"
        if record_key in self.consolidation_records:
            record = self.consolidation_records[record_key]
            record.review_count += 1
            record.last_reviewed = datetime.now()
        
        logger.debug(
            f"Review recorded for {skill_id}: quality={quality}, "
            f"next_interval={schedule.interval_days} days"
        )
        
        return schedule
    
    def calculate_memory_decay(
        self,
        consolidation_time: datetime,
        last_review: Optional[datetime] = None
    ) -> float:
        """Calculate memory decay for a skill.
        
        Args:
            consolidation_time: When skill was consolidated
            last_review: Last review time (if None, uses consolidation_time)
        
        Returns:
            Decay factor (0-1, where 1 is full memory)
        """
        reference_time = last_review or consolidation_time
        days_passed = (datetime.now() - reference_time).days
        
        # Exponential decay: memory = e^(-decay_rate * days)
        decay = math.exp(-self.memory_decay_rate * days_passed / 365.0)
        
        return max(0.0, min(1.0, decay))
    
    def adjust_skill_confidence(
        self,
        current_confidence: float,
        consolidation_time: datetime,
        last_review: Optional[datetime] = None
    ) -> float:
        """Adjust confidence based on memory decay.
        
        Args:
            current_confidence: Current confidence level (0-1)
            consolidation_time: When skill was consolidated
            last_review: Last review time
        
        Returns:
            Adjusted confidence (0-1)
        """
        decay_factor = self.calculate_memory_decay(consolidation_time, last_review)
        adjusted = current_confidence * decay_factor
        
        return max(0.0, min(1.0, adjusted))
    
    def get_consolidation_status(
        self,
        user_id: str
    ) -> Dict[str, any]:
        """Get consolidation status for user.
        
        Args:
            user_id: User ID
        
        Returns:
            Status dict with statistics
        """
        user_records = [
            r for r in self.consolidation_records.values()
            if r.user_id == user_id
        ]
        
        user_schedules = [
            s for s in self.schedules.values()
            if s.user_id == user_id
        ]
        
        if not user_records:
            return {
                "user_id": user_id,
                "total_consolidated": 0,
                "average_consolidation_strength": 0.0,
                "total_scheduled_reviews": 0,
                "pending_reviews": 0
            }
        
        now = datetime.now()
        pending = sum(1 for s in user_schedules if s.next_review_time <= now)
        
        return {
            "user_id": user_id,
            "total_consolidated": len(user_records),
            "average_consolidation_strength": (
                sum(r.consolidation_strength for r in user_records) / len(user_records)
            ),
            "total_scheduled_reviews": len(user_schedules),
            "pending_reviews": pending,
            "total_reviews_completed": sum(s.review_count for s in user_schedules)
        }
    
    def get_skill_consolidation(
        self,
        skill_id: str,
        user_id: str
    ) -> Optional[ConsolidationRecord]:
        """Get consolidation record for skill.
        
        Args:
            skill_id: Skill ID
            user_id: User ID
        
        Returns:
            ConsolidationRecord or None
        """
        key = f"{user_id}_{skill_id}"
        return self.consolidation_records.get(key)
    
    def get_skill_schedule(
        self,
        skill_id: str,
        user_id: str
    ) -> Optional[SpacedRepetitionSchedule]:
        """Get schedule for skill.
        
        Args:
            skill_id: Skill ID
            user_id: User ID
        
        Returns:
            SpacedRepetitionSchedule or None
        """
        key = f"{user_id}_{skill_id}"
        return self.schedules.get(key)
    
    def estimate_mastery(
        self,
        consolidation_strength: float,
        review_count: int,
        quality_scores: List[int]
    ) -> float:
        """Estimate mastery level based on consolidation metrics.
        
        Args:
            consolidation_strength: Consolidation strength (0-1)
            review_count: Number of reviews
            quality_scores: List of quality scores
        
        Returns:
            Mastery estimate (0-1)
        """
        # Base mastery from consolidation
        mastery = consolidation_strength * 0.4
        
        # Add review component (more reviews = higher mastery)
        review_score = min(1.0, review_count / 10.0) * 0.3
        
        # Add quality component
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            quality_score = (avg_quality / 5.0) * 0.3
        else:
            quality_score = 0.0
        
        mastery = mastery + review_score + quality_score
        
        return max(0.0, min(1.0, mastery))
    
    def get_consolidation_insights(
        self,
        user_id: str
    ) -> Dict[str, any]:
        """Get insights about consolidation progress.
        
        Args:
            user_id: User ID
        
        Returns:
            Dict with insights
        """
        user_records = [
            r for r in self.consolidation_records.values()
            if r.user_id == user_id
        ]
        
        if not user_records:
            return {
                "user_id": user_id,
                "insights": "No consolidated skills yet"
            }
        
        # Find strongest/weakest skills
        strongest = max(user_records, key=lambda r: r.consolidation_strength)
        weakest = min(user_records, key=lambda r: r.consolidation_strength)
        
        # Find most reviewed skills
        user_schedules = [
            s for s in self.schedules.values()
            if s.user_id == user_id
        ]
        
        most_reviewed = (
            max(user_schedules, key=lambda s: s.review_count)
            if user_schedules else None
        )
        
        return {
            "user_id": user_id,
            "total_consolidated": len(user_records),
            "strongest_skill": {
                "skill_id": strongest.skill_id,
                "skill_name": strongest.skill_name,
                "strength": strongest.consolidation_strength
            },
            "weakest_skill": {
                "skill_id": weakest.skill_id,
                "skill_name": weakest.skill_name,
                "strength": weakest.consolidation_strength
            },
            "most_reviewed_skill": {
                "skill_id": most_reviewed.skill_id,
                "review_count": most_reviewed.review_count
            } if most_reviewed else None,
            "average_consolidation_strength": (
                sum(r.consolidation_strength for r in user_records) / len(user_records)
            )
        }
