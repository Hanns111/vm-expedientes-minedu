"""Backend package."""

from pathlib import Path

# Add the project root to Python path
import sys
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))