"""Limbic System Module - Safety constraints and danger assessment.

The Limbic System of OpenERB handles safety evaluation, danger assessment,
and two-factor confirmation for high-risk actions.
"""

from .safety_evaluator import SafetyEvaluator, SafetyLevel, SafetyCheck
from .danger_assessment import DangerAssessor, DangerLevel, DangerAssessment
from .confirmation_manager import ConfirmationManager, ConfirmationRequest, ConfirmationStatus

__all__ = [
    # Safety Evaluator
    "SafetyEvaluator",
    "SafetyLevel",
    "SafetyCheck",
    # Danger Assessor
    "DangerAssessor",
    "DangerLevel",
    "DangerAssessment",
    # Confirmation Manager
    "ConfirmationManager",
    "ConfirmationRequest",
    "ConfirmationStatus",
]
