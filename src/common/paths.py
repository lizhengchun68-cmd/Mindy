from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_path(relative: str) -> Path:
    return PROJECT_ROOT / relative
