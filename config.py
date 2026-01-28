from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
MEDIA_ROOT = os.getenv("MEDIA_ROOT", str(BASE_DIR / "media" / "models"))
