"""Model resolver for mapping agents to their optimal LLM models."""

from app.config import settings

# Default model assignments: mini for fast/cheap tasks, full for complex reasoning
_DEFAULT_MODELS: dict[str, str] = {
    "router": "gpt-4.1-mini",
    "general": "gpt-4.1-mini",
    "creative": "gpt-4.1-mini",
    "image": "gpt-4.1-mini",
    "code": "gpt-4.1",
    "research": "gpt-4.1",
    "data": "gpt-4.1",
}

# Environment variable overrides from settings
_ENV_OVERRIDES: dict[str, str] = {
    "router": settings.MODEL_ROUTER,
    "general": settings.MODEL_GENERAL,
    "creative": settings.MODEL_CREATIVE,
    "image": settings.MODEL_IMAGE,
    "code": settings.MODEL_CODE,
    "research": settings.MODEL_RESEARCH,
    "data": settings.MODEL_DATA,
}


def resolve_model(agent_name: str) -> str:
    """Return the best model for a given agent.

    Resolution order:
    1. Environment override (MODEL_CODE, etc.)
    2. Default assignment (mini vs full)
    3. Empty string (lets LLMService use the global default)

    Args:
        agent_name: Name of the agent (e.g. "code", "router").

    Returns:
        Model string to pass to LLMService, or empty string for default.
    """
    env_override = _ENV_OVERRIDES.get(agent_name, "")
    if env_override:
        return env_override

    default = _DEFAULT_MODELS.get(agent_name, "")
    return default
