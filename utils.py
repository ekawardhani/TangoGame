"""Small helper functions used by several modules."""

import re
from pathlib import Path
from gameconfig import BASE_DIR


def slugify(text: str) -> str:
    """Convert text into a safe filename part."""
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "card"


def rel_path(path: Path) -> str:
    """Return a path relative to the project folder for HTML use."""
    return str(path.relative_to(BASE_DIR)).replace("\\", "/")
