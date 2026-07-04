from opencode_client.client import call_opencode, call_opencode_json
from openai_client.client import call_openai, call_openai_json

from model_constants import (
    PROVIDER_CLAUDE,
    PROVIDER_OPENAI
)

# ---------------------------------------------------------
# MODEL SELECTION RULES
# ---------------------------------------------------------

def resolve_provider(model: str):
    if model.startswith("claude"):
        return PROVIDER_CLAUDE
    if model.startswith("gpt"):
        return PROVIDER_OPENAI
    raise RuntimeError(f"Unknown model provider for: {model}")

def select_model_for_planning(model_config):
    model = model_config["planning_model"]
    return model, resolve_provider(model)

def select_model_for_fixloop(model_config):
    model = model_config["fixloop_model"]
    return model, resolve_provider(model)

def select_model_for_decomposition(model_config):
    model = model_config["decomposition_model"]
    return model, resolve_provider(model)

def select_model_for_task_execution(task_title: str, repo_type: str, model_config: object):
    title = task_title.lower()

    if "fix" in title or "repair" in title:
        model = model_config["fixloop_model"]
        return model, resolve_provider(model)

    # NOTE: repo_type/keyword checks used to branch here, but every
    # branch resolved to the same model_config["execution_model"] --
    # there is currently only one execution model, so nothing actually
    # varied by repo_type or by keyword. Left as a single fallback
    # rather than dead branches that look like they do something they
    # don't. If per-repo-type or per-keyword model routing is wanted
    # later, this is the place to reintroduce it -- with a config
    # value it can actually select between.
    model = model_config["execution_model"]
    return model, resolve_provider(model)


# ---------------------------------------------------------
# UNIFIED CALL WRAPPER
# ---------------------------------------------------------

async def call_model(prompt: str, model: str, provider: str):
    if provider == PROVIDER_CLAUDE:
        return await call_opencode(prompt, model=model)
    return await call_openai(prompt, model=model)


async def call_model_json(prompt: str, model: str, provider: str):
    if provider == PROVIDER_CLAUDE:
        return await call_opencode_json(prompt, model=model)
    return await call_openai_json(prompt, model=model)
