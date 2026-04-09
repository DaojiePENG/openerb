"""
Interface module for OpenERB - Main user interaction layer.

This module provides the orchestration layer that:
  - Connects all neural modules (PrefrontalCortex, MotorCortex, Hippocampus, etc.)
  - Manages user interaction and natural conversation
  - Delegates all learning/memory/execution to appropriate brain modules
  - Provides the primary entry point for users to interact with the system

Architecture principle: Interface is PURE ORCHESTRATION - it does not implement
features itself, but rather coordinates the neural modules that do.
"""

from .embodied_brain_interface import EmbodiedBrainInterface, start_embodied_brain

__all__ = ['EmbodiedBrainInterface', 'start_embodied_brain']