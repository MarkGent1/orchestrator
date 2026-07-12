from dataclasses import dataclass, field
from typing import List

@dataclass
class ContextProfile:
    required_layers: List[str]
    forbidden_layers: List[str] = field(default_factory=list)
