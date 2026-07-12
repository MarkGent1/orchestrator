import argparse
import asyncio
import yaml
from pathlib import Path

from supervisor.supervisor_agent import SupervisorAgent

from model_constants import (
    DEFAULT_PLANNING_MODEL,
    DEFAULT_DECOMPOSITION_MODEL,
    DEFAULT_EXECUTION_MODEL,
    DEFAULT_FIXLOOP_MODEL,
)

# -------------------------------------------------------------
# python main.py 400 --repo D:\git\mav\mav-user-api-sdlc-poc
#   --planning-model gpt-5.4-mini
#   --fixloop-model gpt-5.4-mini
#   --decomposition-model gpt-5.4-mini
#   --execution-model gpt-5.4-mini
# -------------------------------------------------------------

async def main():
    # ---------------------------------------------------------
    # CLI validation
    # ---------------------------------------------------------
    parser = argparse.ArgumentParser()

    parser.add_argument("work_item_id", type=int)
    parser.add_argument("--repo", required=True)

    # NOTE: these default to None (not the hardcoded model constants) so
    # the fallback chain below can tell "not passed on the CLI" apart
    # from "explicitly passed". If these defaulted to the model
    # constants directly, `args.planning_model` etc. would always be
    # truthy and the values loaded from models.yaml a few lines down
    # would silently never be used.
    parser.add_argument("--planning-model", default=None)
    parser.add_argument("--fixloop-model", default=None)
    parser.add_argument("--decomposition-model", default=None)
    parser.add_argument("--execution-model", default=None)

    args = parser.parse_args()

    work_item_id = args.work_item_id
    repo_path = Path(args.repo).resolve()

    # ---------------------------------------------------------
    # Load default model config from models.yaml
    # ---------------------------------------------------------
    models_yaml_path = Path(__file__).parent / "models.yaml"

    if models_yaml_path.exists():
        with open(models_yaml_path, "r", encoding="utf-8") as f:
            default_model_config = yaml.safe_load(f)
    else:
        default_model_config = {
            "planning_model": DEFAULT_PLANNING_MODEL,
            "decomposition_model": DEFAULT_DECOMPOSITION_MODEL,
            "execution_model": DEFAULT_EXECUTION_MODEL,
            "fixloop_model": DEFAULT_FIXLOOP_MODEL,
        }

    # ---------------------------------------------------------
    # CLI overrides YAML defaults, which override hardcoded defaults
    # ---------------------------------------------------------
    model_config = {
        "planning_model": args.planning_model or default_model_config.get("planning_model", DEFAULT_PLANNING_MODEL),
        "fixloop_model": args.fixloop_model or default_model_config.get("fixloop_model", DEFAULT_FIXLOOP_MODEL),
        "decomposition_model": args.decomposition_model or default_model_config.get("decomposition_model", DEFAULT_DECOMPOSITION_MODEL),
        "execution_model": args.execution_model or default_model_config.get("execution_model", DEFAULT_EXECUTION_MODEL),
    }

    # ---------------------------------------------------------
    # Startup Banner: Show Selected Models
    # ---------------------------------------------------------
    print("\n==================== ORCHESTRATOR MODEL CONFIG ====================")
    print(f"Planning Model:      {model_config['planning_model']}")
    print(f"Decomposition Model: {model_config['decomposition_model']}")
    print(f"Execution Model:     {model_config['execution_model']}")
    print(f"FixLoop Model:       {model_config['fixloop_model']}")
    print("====================================================================\n")

    # ---------------------------------------------------------
    # Run SupervisorAgent
    # ---------------------------------------------------------
    supervisor = SupervisorAgent(
        repo_path=repo_path,
        work_item_id=work_item_id,
        model_config=model_config,
    )

    await supervisor.run()


if __name__ == "__main__":
    asyncio.run(main())
