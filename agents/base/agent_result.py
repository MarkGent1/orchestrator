from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class AgentError:
    type: str
    message: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class AgentResult:
    success: bool
    payload: Optional[Any] = None
    error: Optional[AgentError] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
