from opencode.client import call_opencode, call_opencode_json
from openai.client import call_openai, call_openai_json

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
    provider = resolve_provider(model)
    return model, provider

def select_model_for_fixloop(model_config):
    model = model_config["fixloop_model"]
    provider = resolve_provider(model)
    return model, provider

def select_model_for_decomposition(model_config):
    model = model_config["decomposition_model"]
    provider = resolve_provider(model)
    return model, provider

def select_model_for_task_execution(task_title: str, repo_type: str, model_config: object):
    title = task_title.lower()

    # FixLoop tasks
    if "fix" in title or "repair" in title:
        model = model_config["fixloop_model"]
        return model, resolve_provider(model)

    # Backend tasks often need deeper reasoning
    if repo_type == "backend":
        if any(x in title for x in ["controller", "service", "handler", "domain"]):
            model = model_config["execution_model"]
            return model, resolve_provider(model)

    # Frontend tasks are usually fine with GPT‑mini
    if repo_type == "frontend":
        model = model_config["execution_model"]
        return model, resolve_provider(model)

    # Default
    model = model_config["execution_model"]
    return model, resolve_provider(model)


# ---------------------------------------------------------
# UNIFIED CALL WRAPPER
# ---------------------------------------------------------

async def call_model(prompt: str, model: str, provider: str):
    if provider == PROVIDER_CLAUDE:
        return await call_opencode(prompt, model=model)
    elif provider == PROVIDER_OPENAI:
        return await call_openai(prompt, model=model)
    else:
        raise RuntimeError(f"Unknown provider: {provider}")


async def call_model_json(prompt: str, model: str, provider: str):
    if provider == PROVIDER_CLAUDE:
        return await call_opencode_json(prompt, model=model)
    elif provider == PROVIDER_OPENAI:
        return await call_openai_json(prompt, model=model)
    else:
        raise RuntimeError(f"Unknown provider: {provider}")
