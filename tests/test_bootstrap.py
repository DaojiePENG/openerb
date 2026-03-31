"""
Test bootstrap initialization system.
"""

import pytest
from pathlib import Path
from core.bootstrap import setup_system
from core import get_storage_config


class TestBootstrap:
    """Tests for bootstrap initialization."""
    
    def test_get_storage_config(self):
        """Test storage config retrieval."""
        config = get_storage_config()
        assert config is not None
        assert config.db_path is not None
    
    def test_setup_system_defaults(self):
        """Test system setup with defaults."""
        setup_system(robot_type="G1", debug=False)
        # If we got here without exception, setup succeeded
        assert True
