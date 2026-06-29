"""Load markdown prompt templates for LLM steps."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


def load_prompt(name: str) -> str:
    """Load ``app/agent/prompts/{name}.md``."""
    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8")
