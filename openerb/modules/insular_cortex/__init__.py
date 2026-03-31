"""Insular Cortex - Robot body self-awareness module."""

from openerb.modules.insular_cortex.cortex import InsularCortex
from openerb.modules.insular_cortex.body_detector import BodyDetector
from openerb.modules.insular_cortex.capability_mapper import CapabilityMapper
from openerb.modules.insular_cortex.skill_classifier import SkillClassifier

__all__ = [
    "InsularCortex",
    "BodyDetector",
    "CapabilityMapper",
    "SkillClassifier",
]
