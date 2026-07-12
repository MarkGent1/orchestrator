from dataclasses import dataclass
from typing import Optional

@dataclass
class ReliabilityProfile:
    retries: int = 1
    strict_mode: bool = False
    fallback_model: Optional[str] = None
    fixloop_enabled: bool = False
