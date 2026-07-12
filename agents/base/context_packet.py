from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class ContextPacket:
    global_ctx: Optional[Dict[str, Any]] = None
    task_ctx: Optional[Dict[str, Any]] = None
    local_ctx: Optional[Dict[str, Any]] = None
    micro_ctx: Optional[Dict[str, Any]] = None

    def layer_names(self) -> List[str]:
        layers = []
        if self.global_ctx is not None:
            layers.append("global")
        if self.task_ctx is not None:
            layers.append("task")
        if self.local_ctx is not None:
            layers.append("local")
        if self.micro_ctx is not None:
            layers.append("micro")
        return layers
