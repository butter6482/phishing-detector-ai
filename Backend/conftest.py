import sys
from pathlib import Path

# Permite `import src.*` al correr pytest desde Backend/
sys.path.insert(0, str(Path(__file__).resolve().parent))
