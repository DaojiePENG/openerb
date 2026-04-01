"""Hippocampus Module - Long-term Memory System."""

from .learning_profile import (
    LearningPreferences,
    SkillProgress,
    UserLearningProfile,
    LearningProfileManager
)
from .learning_history import (
    LearningEvent,
    LearningSession,
    LearningHistoryTracker
)
from .consolidation_engine import (
    ConsolidationRecord,
    SpacedRepetitionSchedule,
    ConsolidationEngine
)
from .competency_metrics import (
    CompetencyScore,
    CompetencyTier,
    CompetencyMetrics
)
from .hippocampus import Hippocampus

__all__ = [
    # Learning Profile
    "LearningPreferences",
    "SkillProgress",
    "UserLearningProfile",
    "LearningProfileManager",
    # Learning History
    "LearningEvent",
    "LearningSession",
    "LearningHistoryTracker",
    # Consolidation
    "ConsolidationRecord",
    "SpacedRepetitionSchedule",
    "ConsolidationEngine",
    # Competency
    "CompetencyScore",
    "CompetencyTier",
    "CompetencyMetrics",
    # Main API
    "Hippocampus"
]
