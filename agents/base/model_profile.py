from dataclasses import dataclass

@dataclass
class ModelProfile:
    name: str
    temperature: float = 0.0
    max_tokens: int = 4096
    mode: str = "reasoning"  # "reasoning" | "editing" | "debugging" | "summarisation"
