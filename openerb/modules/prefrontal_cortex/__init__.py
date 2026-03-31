"""Prefrontal Cortex module - User interaction and intent understanding.

This module provides the entry point for all user interactions with OpenERB.
It handles multi-modal input processing, intent recognition, and task decomposition.
"""

from openerb.modules.prefrontal_cortex.cortex import PrefrontalCortex
from openerb.modules.prefrontal_cortex.intent_parser import IntentParser
from openerb.modules.prefrontal_cortex.task_decomposer import TaskDecomposer
from openerb.modules.prefrontal_cortex.context_manager import ContextManager

__all__ = [
    "PrefrontalCortex",
    "IntentParser",
    "TaskDecomposer",
    "ContextManager",
]
