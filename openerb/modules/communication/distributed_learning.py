from typing import Dict, List

from openerb.core.logger import get_logger
from openerb.core.types import ExperienceReport

logger = get_logger("distributed_learning")


class DistributedLearningManager:
    """Aggregates experience reports and produces distributed learning insights."""

    def __init__(self):
        self.reports: List[ExperienceReport] = []

    def submit_report(self, report: ExperienceReport):
        logger.debug("Submitting report for skill %s from node %s", report.skill_id, report.node_id)
        self.reports.append(report)

    def aggregate_for_skill(self, skill_id: str) -> Dict[str, float]:
        filtered = [r for r in self.reports if r.skill_id == skill_id]
        if not filtered:
            logger.warning("No reports found for skill %s", skill_id)
            return {
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "confidence": 0.0,
                "sample_size": 0,
            }

        total = len(filtered)
        successes = sum(1 for r in filtered if r.success)
        duration = sum(r.duration_ms for r in filtered)
        confidence = sum(r.confidence for r in filtered)

        result = {
            "success_rate": successes / total,
            "average_duration_ms": duration / total,
            "average_confidence": confidence / total,
            "sample_size": total,
        }
        logger.info("Aggregated reports for skill %s: %s", skill_id, result)
        return result

    def get_trending_skills(self, top_n: int = 5) -> List[str]:
        from collections import defaultdict

        stats = defaultdict(lambda: {"successes": 0, "total": 0})
        for report in self.reports:
            stats[report.skill_id]["total"] += 1
            if report.success:
                stats[report.skill_id]["successes"] += 1

        if not stats:
            return []

        sorted_skills = sorted(
            stats.items(),
            key=lambda kv: kv[1]["successes"] / kv[1]["total"] if kv[1]["total"] > 0 else 0,
            reverse=True,
        )
        result = [skill_id for skill_id, _ in sorted_skills[:top_n]]
        logger.debug("Trending skills computed: %s", result)
        return result
