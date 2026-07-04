# ============================================================
# GLOBAL MODEL CONSTANTS
# ============================================================

# Providers
PROVIDER_CLAUDE = "claude"
PROVIDER_OPENAI = "openai"

# Claude Models
CLAUDE_SONNET = "claude-sonnet-4-6"
CLAUDE_HAIKU = "claude-haiku-4-5"

# OpenAI Models
GPT_MINI = "gpt-5.4-mini"

# ============================================================
# DEFAULTS (used by models.yaml fallback)
# ============================================================

DEFAULT_PLANNING_MODEL = CLAUDE_SONNET
DEFAULT_DECOMPOSITION_MODEL = GPT_MINI
DEFAULT_EXECUTION_MODEL = CLAUDE_HAIKU
DEFAULT_FIXLOOP_MODEL = CLAUDE_HAIKU
