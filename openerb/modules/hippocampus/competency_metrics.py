"""Competency Metrics - Skill competency scoring and ranking."""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CompetencyScore:
    """Competency score for a skill."""
    skill_id: str
    skill_name: str
    user_id: str
    overall_score: float  # 0-100
    technical_score: float  # 0-100 (accuracy, success rate)
    consistency_score: float  # 0-100 (reliability, consistency)
    efficiency_score: float  # 0-100 (execution speed)
    learning_velocity: float  # 0-100 (improvement rate)
    timestamp: datetime = None


@dataclass
class CompetencyTier:
    """Competency tier classification."""
    tier: str  # "novice", "intermediate", "advanced", "expert", "master"
    score_range: Tuple[int, int]  # (min, max)
    requirements: List[str]


class CompetencyMetrics:
    """Calculate and track competency metrics for skills."""
    
    # Competency tiers with score ranges
    TIERS = {
        "novice": CompetencyTier("novice", (0, 20), [
            "Basic understanding",
            "Few successful executions",
            "High error rate"
        ]),
        "intermediate": CompetencyTier("intermediate", (20, 40), [
            "Functional execution",
            "Moderate success rate",
            "Some consistency"
        ]),
        "advanced": CompetencyTier("advanced", (40, 70), [
            "Reliable execution",
            "High success rate",
            "Good consistency",
            "Reasonable efficiency"
        ]),
        "expert": CompetencyTier("expert", (70, 90), [
            "Very reliable execution",
            "Very high success rate",
            "Excellent consistency",
            "Efficient execution"
        ]),
        "master": CompetencyTier("master", (90, 100), [
            "Consistently perfect execution",
            "Teaching capability",
            "Optimization expertise"
        ])
    }
    
    def __init__(self):
        """Initialize competency metrics."""
        self.scores: Dict[str, CompetencyScore] = {}
        logger.info("CompetencyMetrics initialized")
    
    def calculate_competency(
        self,
        skill_id: str,
        skill_name: str,
        user_id: str,
        success_rate: float,
        average_duration: float,
        execution_count: int,
        confidence: float,
        learning_velocity: float = 0.0
    ) -> CompetencyScore:
        """Calculate overall competency score.
        
        Args:
            skill_id: Skill ID
            skill_name: Skill name
            user_id: User ID
            success_rate: Success rate (0-1)
            average_duration: Average execution duration (seconds)
            execution_count: Number of executions
            confidence: Confidence level (0-1)
            learning_velocity: Learning velocity (0-1)
        
        Returns:
            CompetencyScore
        """
        # Calculate technical score (accuracy + confidence)
        technical_score = (success_rate * 0.6 + confidence * 0.4) * 100
        
        # Calculate consistency score (based on execution count and success pattern)
        consistency_score = self._calculate_consistency(
            execution_count, success_rate
        )
        
        # Calculate efficiency score (inverse of duration, normalized)
        efficiency_score = self._calculate_efficiency(average_duration)
        
        # Learning velocity score
        velocity_score = min(100, learning_velocity * 100)
        
        # Overall score (weighted average)
        overall_score = (
            technical_score * 0.4 +
            consistency_score * 0.25 +
            efficiency_score * 0.2 +
            velocity_score * 0.15
        )
        
        score = CompetencyScore(
            skill_id=skill_id,
            skill_name=skill_name,
            user_id=user_id,
            overall_score=min(100, max(0, overall_score)),
            technical_score=min(100, max(0, technical_score)),
            consistency_score=min(100, max(0, consistency_score)),
            efficiency_score=min(100, max(0, efficiency_score)),
            learning_velocity=min(100, max(0, velocity_score)),
            timestamp=datetime.now()
        )
        
        # Store score
        key = f"{user_id}_{skill_id}"
        self.scores[key] = score
        
        logger.debug(f"Competency calculated for {skill_name}: {overall_score:.1f}")
        
        return score
    
    def _calculate_consistency(
        self,
        execution_count: int,
        success_rate: float
    ) -> float:
        """Calculate consistency score.
        
        Args:
            execution_count: Number of executions
            success_rate: Success rate (0-1)
        
        Returns:
            Consistency score (0-100)
        """
        import math
        
        # More executions = higher potential for consistency
        execution_factor = min(1.0, math.log(execution_count + 1) / math.log(11))
        
        # Success rate consistency
        rate_factor = success_rate
        
        # Combined consistency score
        consistency = (execution_factor * 0.5 + rate_factor * 0.5) * 100
        
        return min(100, max(0, consistency))
    
    def _calculate_efficiency(self, average_duration: float) -> float:
        """Calculate efficiency score based on execution time.
        
        Args:
            average_duration: Average execution duration (seconds)
        
        Returns:
            Efficiency score (0-100)
        """
        # Reference: 5 seconds is considered highly efficient (score 100)
        # 30 seconds is considered minimal efficiency (score 20)
        # > 60 seconds is very inefficient (score < 10)
        
        if average_duration <= 5:
            efficiency = 100.0
        elif average_duration <= 30:
            # Linear interpolation from 100 to 20
            efficiency = 100 - (average_duration - 5) * (80 / 25)
        elif average_duration <= 60:
            # Linear interpolation from 20 to 5
            efficiency = 20 - (average_duration - 30) * (15 / 30)
        else:
            efficiency = max(0, 5 - (average_duration - 60) * 0.1)
        
        return min(100, max(0, efficiency))
    
    def get_competency_tier(self, overall_score: float) -> str:
        """Get competency tier for score.
        
        Args:
            overall_score: Overall competency score (0-100)
        
        Returns:
            Tier name
        """
        for tier_name, tier in self.TIERS.items():
            if tier.score_range[0] <= overall_score <= tier.score_range[1]:
                return tier_name
        
        return "novice"
    
    def get_score(
        self,
        skill_id: str,
        user_id: str
    ) -> Optional[CompetencyScore]:
        """Get competency score for skill.
        
        Args:
            skill_id: Skill ID
            user_id: User ID
        
        Returns:
            CompetencyScore or None
        """
        key = f"{user_id}_{skill_id}"
        return self.scores.get(key)
    
    def rank_skills(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[CompetencyScore]:
        """Rank user's skills by competency.
        
        Args:
            user_id: User ID
            limit: Maximum skills to return
        
        Returns:
            List of CompetencyScore sorted by overall_score (descending)
        """
        user_scores = [
            s for s in self.scores.values()
            if s.user_id == user_id
        ]
        
        # Sort by overall score, descending
        user_scores.sort(key=lambda s: s.overall_score, reverse=True)
        
        return user_scores[:limit]
    
    def get_user_summary(self, user_id: str) -> Dict:
        """Get competency summary for user.
        
        Args:
            user_id: User ID
        
        Returns:
            Summary dict
        """
        user_scores = [
            s for s in self.scores.values()
            if s.user_id == user_id
        ]
        
        if not user_scores:
            return {
                "user_id": user_id,
                "total_skills": 0,
                "average_competency": 0.0
            }
        
        avg_technical = sum(s.technical_score for s in user_scores) / len(user_scores)
        avg_consistency = sum(s.consistency_score for s in user_scores) / len(user_scores)
        avg_efficiency = sum(s.efficiency_score for s in user_scores) / len(user_scores)
        avg_overall = sum(s.overall_score for s in user_scores) / len(user_scores)
        
        # Count by tier
        tier_distribution = {}
        for score in user_scores:
            tier = self.get_competency_tier(score.overall_score)
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        return {
            "user_id": user_id,
            "total_skills": len(user_scores),
            "average_technical_score": avg_technical,
            "average_consistency_score": avg_consistency,
            "average_efficiency_score": avg_efficiency,
            "average_overall_score": avg_overall,
            "tier_distribution": tier_distribution,
            "top_skill": user_scores[0] if user_scores else None
        }
    
    def recommend_practice_skills(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Tuple[str, str, float]]:
        """Recommend skills to practice based on competency.
        
        Args:
            user_id: User ID
            limit: Maximum recommendations
        
        Returns:
            List of (skill_id, skill_name, gap) tuples
        """
        user_scores = [
            s for s in self.scores.values()
            if s.user_id == user_id
        ]
        
        if not user_scores:
            return []
        
        # Find skills with lowest scores (most need practice)
        skills_by_gap = [
            (s.skill_id, s.skill_name, 100 - s.overall_score)
            for s in user_scores
        ]
        
        # Sort by gap (descending)
        skills_by_gap.sort(key=lambda x: x[2], reverse=True)
        
        return skills_by_gap[:limit]
    
    def get_skill_strengths(
        self,
        skill_id: str,
        user_id: str
    ) -> Optional[Dict]:
        """Get detailed strength analysis for skill.
        
        Args:
            skill_id: Skill ID
            user_id: User ID
        
        Returns:
            Dict with strength analysis or None
        """
        score = self.get_score(skill_id, user_id)
        
        if not score:
            return None
        
        tier = self.get_competency_tier(score.overall_score)
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        STRENGTH_THRESHOLD = 75  # Score threshold for strength
        WEAKNESS_THRESHOLD = 40  # Score threshold for weakness
        
        if score.technical_score >= STRENGTH_THRESHOLD:
            strengths.append("Excellent accuracy and success rate")
        elif score.technical_score < WEAKNESS_THRESHOLD:
            weaknesses.append("Low accuracy and success rate")
        
        if score.consistency_score >= STRENGTH_THRESHOLD:
            strengths.append("Highly consistent execution")
        elif score.consistency_score < WEAKNESS_THRESHOLD:
            weaknesses.append("Inconsistent execution")
        
        if score.efficiency_score >= STRENGTH_THRESHOLD:
            strengths.append("Very efficient execution")
        elif score.efficiency_score < WEAKNESS_THRESHOLD:
            weaknesses.append("Poor execution efficiency")
        
        if score.learning_velocity >= STRENGTH_THRESHOLD:
            strengths.append("Rapid learning improvement")
        elif score.learning_velocity < WEAKNESS_THRESHOLD:
            weaknesses.append("Slow learning progress")
        
        return {
            "skill_id": skill_id,
            "skill_name": score.skill_name,
            "overall_score": score.overall_score,
            "tier": tier,
            "technical_score": score.technical_score,
            "consistency_score": score.consistency_score,
            "efficiency_score": score.efficiency_score,
            "learning_velocity": score.learning_velocity,
            "strengths": strengths if strengths else ["Balanced competency"],
            "weaknesses": weaknesses if weaknesses else ["No major weaknesses"]
        }
    
    def calculate_learning_velocity(
        self,
        previous_score: float,
        current_score: float,
        time_period_days: int
    ) -> float:
        """Calculate learning velocity (improvement rate).
        
        Args:
            previous_score: Previous competency score
            current_score: Current competency score
            time_period_days: Time period in days
        
        Returns:
            Learning velocity (score points per day)
        """
        if time_period_days <= 0:
            return 0.0
        
        velocity = (current_score - previous_score) / time_period_days
        
        return max(0.0, velocity)
    
    def predict_mastery_time(
        self,
        current_score: float,
        learning_velocity: float
    ) -> Optional[int]:
        """Predict days until mastery (score >= 70).
        
        Args:
            current_score: Current competency score
            learning_velocity: Learning velocity (score points per day)
        
        Returns:
            Estimated days until mastery or None
        """
        MASTERY_THRESHOLD = 70
        
        if current_score >= MASTERY_THRESHOLD:
            return 0
        
        if learning_velocity <= 0:
            return None  # Cannot predict without positive velocity
        
        days_needed = (MASTERY_THRESHOLD - current_score) / learning_velocity
        
        return max(1, int(days_needed))
    
    def adjust_competency(
        self,
        skill_id: str,
        user_id: str,
        adjustment_factor: float
    ) -> Optional[CompetencyScore]:
        """Adjust competency score by factor.
        
        Args:
            skill_id: Skill ID
            user_id: User ID
            adjustment_factor: Multiplicative factor (e.g., 1.1 = 10% increase)
        
        Returns:
            Adjusted CompetencyScore or None
        """
        score = self.get_score(skill_id, user_id)
        
        if not score:
            return None
        
        # Apply adjustment to all scores
        score.overall_score = min(100, max(0, score.overall_score * adjustment_factor))
        score.technical_score = min(100, max(0, score.technical_score * adjustment_factor))
        score.consistency_score = min(100, max(0, score.consistency_score * adjustment_factor))
        score.efficiency_score = min(100, max(0, score.efficiency_score * adjustment_factor))
        score.learning_velocity = min(100, max(0, score.learning_velocity * adjustment_factor))
        score.timestamp = datetime.now()
        
        logger.debug(f"Adjusted competency for {skill_id}: {adjustment_factor}")
        
        return score
