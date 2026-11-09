import sys
from pathlib import Path

# allow `pytest` without `pip install -e .`
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
