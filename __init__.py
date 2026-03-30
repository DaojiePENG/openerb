"""
OpenERB - Open Embodied Robot Brain (openerb)
An AI-powered self-evolving robot control system with brain-inspired architecture.
"""

__version__ = "0.1.0"
__author__ = "OpenERB Project"
__project_name__ = "openerb"
__description__ = "Open Embodied Robot Brain - Self-Evolving Robot Control System"

from . import core
from . import modules

__all__ = ["core", "modules", "__version__", "__author__", "__project_name__"]
