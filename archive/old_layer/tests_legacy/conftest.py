"""
conftest.py - Setup untuk pytest
==================================
"""

import sys
from pathlib import Path

# Add parent folder to path
sys.path.insert(0, str(Path(__file__).parent.parent))