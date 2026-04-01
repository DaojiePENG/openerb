"""Skill Scorer - Performance tracking and rating system.

Tracks execution metrics, calculates performance scores, and
maintains competency ratings for skills.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of a skill execution."""

    SUCCESS = "success"
    PARTIAL = "partial"  # Partially successful
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class SkillExecution:
    """Record of a single skill execution."""

    execution_id: str
    skill_id: str
    status: ExecutionStatus
    start_time: datetime
    end_time: datetime
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str] = None
    success_score: float = 1.0  # 0.0-1.0


class SkillScorer:
    """Track and score skill performance.
    
    Maintains execution history and calculates metrics:
    - Success rate
    - Execution time statistics
    - Competency scores
    - Ranking
    
    Example:
        >>> scorer = SkillScorer()
        >>> execution = SkillExecution(...)
        >>> scorer.record_execution(execution)
        >>> metrics = scorer.get_skill_metrics("skill_123")
        >>> ranking = scorer.rank_skills(limit=10)
    """

    def __init__(self):
        """Initialize skill scorer."""
        self.executions: Dict[str, List[SkillExecution]] = {}  # skill_id -> executions
        self.competency_scores: Dict[str, float] = {}  # skill_id -> final score
        logger.debug("Initialized SkillScorer")

    def record_execution(
        self,
        skill_id: str,
        status: ExecutionStatus,
        duration_ms: int,
        parameters: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        success_score: float = 1.0,
    ) -> str:
        """Record a skill execution.

        Args:
            skill_id: The skill being executed
            status: Execution status
            duration_ms: Execution duration in milliseconds
            parameters: Parameters used for execution
            result: Execution result data
            error_message: Error message if any
            success_score: Score from 0.0 (failure) to 1.0 (perfect)

        Returns:
            Execution ID
        """
        import uuid

        execution_id = str(uuid.uuid4())[:12]
        now = datetime.now()
        end_time = now + timedelta(milliseconds=duration_ms)

        execution = SkillExecution(
            execution_id=execution_id,
            skill_id=skill_id,
            status=status,
            start_time=now,
            end_time=end_time,
            parameters=parameters,
            result=result,
            error_message=error_message,
            success_score=success_score if status == ExecutionStatus.SUCCESS else 0.0,
        )

        # Store execution
        if skill_id not in self.executions:
            self.executions[skill_id] = []
        self.executions[skill_id].append(execution)

        # Update competency score
        self._update_competency_score(skill_id)

        logger.info(
            f"Recorded execution {execution_id} for skill {skill_id}: {status.value}"
        )
        return execution_id

    def get_skill_metrics(self, skill_id: str) -> Dict[str, Any]:
        """Get performance metrics for a skill.

        Args:
            skill_id: The skill ID

        Returns:
            Dictionary with performance metrics
        """
        if skill_id not in self.executions:
            return {
                "total_executions": 0,
                "success_rate": 0.0,
                "competency_score": 0.0,
                "average_duration_ms": 0,
                "status_breakdown": {},
            }

        executions = self.executions[skill_id]
        total = len(executions)

        # Calculate success rate
        successful = sum(
            1 for e in executions if e.status == ExecutionStatus.SUCCESS
        )
        success_rate = successful / total if total > 0 else 0.0

        # Calculate average duration
        durations = [
            (e.end_time - e.start_time).total_seconds() * 1000
            for e in executions
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Status breakdown
        status_breakdown = {}
        for status in ExecutionStatus:
            count = sum(1 for e in executions if e.status == status)
            status_breakdown[status.value] = count

        return {
            "total_executions": total,
            "success_rate": success_rate,
            "competency_score": self.competency_scores.get(skill_id, 0.0),
            "average_duration_ms": int(avg_duration),
            "status_breakdown": status_breakdown,
            "first_execution": executions[0].start_time.isoformat(),
            "last_execution": executions[-1].start_time.isoformat(),
        }

    def rank_skills(
        self,
        limit: Optional[int] = None,
        metric: str = "competency_score",
    ) -> List[Dict[str, Any]]:
        """Rank skills by performance metric.

        Args:
            limit: Maximum number of skills to return
            metric: Metric to rank by (competency_score, success_rate, execution_count)

        Returns:
            Ranked list of skills with metrics
        """
        rankings = []

        for skill_id in self.executions.keys():
            metrics = self.get_skill_metrics(skill_id)
            
            if metric == "competency_score":
                score = metrics["competency_score"]
            elif metric == "success_rate":
                score = metrics["success_rate"]
            elif metric == "execution_count":
                score = metrics["total_executions"]
            else:
                score = metrics["competency_score"]

            rankings.append({
                "skill_id": skill_id,
                "score": score,
                "metrics": metrics,
            })

        # Sort by score descending
        rankings.sort(key=lambda x: x["score"], reverse=True)

        if limit:
            rankings = rankings[:limit]

        return rankings

    def get_execution_history(
        self,
        skill_id: str,
        last_n: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get execution history for a skill.

        Args:
            skill_id: The skill ID
            last_n: Return last N executions

        Returns:
            List of executions
        """
        if skill_id not in self.executions:
            return []

        executions = self.executions[skill_id]
        if last_n:
            executions = executions[-last_n:]

        return [
            {
                "execution_id": e.execution_id,
                "status": e.status.value,
                "time": e.start_time.isoformat(),
                "duration_ms": int((e.end_time - e.start_time).total_seconds() * 1000),
                "success_score": e.success_score,
                "error": e.error_message,
            }
            for e in executions
        ]

    def get_recent_failures(
        self,
        time_window_hours: int = 24,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get recent skill failures.

        Args:
            time_window_hours: Only look at last N hours
            limit: Maximum number of failures to return

        Returns:
            List of recent failures
        """
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        failures = []

        for skill_id, executions in self.executions.items():
            for execution in executions:
                if (
                    execution.status != ExecutionStatus.SUCCESS
                    and execution.start_time > cutoff_time
                ):
                    failures.append({
                        "skill_id": skill_id,
                        "execution_id": execution.execution_id,
                        "status": execution.status.value,
                        "time": execution.start_time.isoformat(),
                        "error": execution.error_message,
                    })

        # Sort by time descending and limit
        failures.sort(key=lambda x: x["time"], reverse=True)
        return failures[:limit]

    def get_trending_skills(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get skills with trending improved performance.

        Args:
            limit: Number of trending skills to return

        Returns:
            Skills with improving trend
        """
        trending = []

        for skill_id in self.executions.keys():
            executions = self.executions[skill_id]
            if len(executions) < 2:
                continue

            # Split into early and recent
            midpoint = len(executions) // 2
            early_rate = sum(
                1 for e in executions[:midpoint]
                if e.status == ExecutionStatus.SUCCESS
            ) / midpoint if midpoint > 0 else 0

            recent_rate = sum(
                1 for e in executions[midpoint:]
                if e.status == ExecutionStatus.SUCCESS
            ) / (len(executions) - midpoint) if len(executions) > midpoint else 0

            # Calculate trend
            trend = recent_rate - early_rate

            if trend > 0:  # Improving
                trending.append({
                    "skill_id": skill_id,
                    "trend": trend,
                    "early_success_rate": early_rate,
                    "recent_success_rate": recent_rate,
                    "execution_count": len(executions),
                })

        # Sort by trend and return top
        trending.sort(key=lambda x: x["trend"], reverse=True)
        return trending[:limit]

    def _update_competency_score(self, skill_id: str) -> None:
        """Update competency score for a skill.

        Args:
            skill_id: The skill ID
        """
        if skill_id not in self.executions:
            self.competency_scores[skill_id] = 0.0
            return

        executions = self.executions[skill_id]
        
        # Competency score = (success_rate * 0.7) + (consistency * 0.3)
        total = len(executions)
        successful = sum(
            1 for e in executions if e.status == ExecutionStatus.SUCCESS
        )
        success_rate = successful / total if total > 0 else 0.0

        # Consistency: how stable is the success rate
        # Recent window has more weight
        recent_window = min(10, total)
        recent_success = sum(
            1 for e in executions[-recent_window:]
            if e.status == ExecutionStatus.SUCCESS
        ) / recent_window

        competency = (success_rate * 0.5) + (recent_success * 0.5)
        self.competency_scores[skill_id] = competency
