from datetime import datetime, timezone
from json import tool
from typing import Any, Literal
from pydantic import BaseModel, Field

class ActionKernel:
    def __init__(self, tool_registry, state_manager):
        self.tool_registry = tool_registry
        self.state_manager = state_manager

    def execute(
            self,
            domain: str,
            tool_name: str,
            arguments: dict
    ) -> ActionOutcome:
        tool = self.tool_registry.get(domain, tool_name)
        validated = tool.args_model.model_validate(arguments)
        outcome = tool.handler(**validated.model_dump())

        if not isinstance(outcome, ActionOutcome):
            raise TypeError(
                f"{domain}.{tool_name} did not return ActionOutcome."
            )

        if outcome.status == "success":
            self.state_manager.apply(outcome)

        return outcome

class ActionOutcome(BaseModel):
    status: Literal["success", "failed", "declined"] # add a pending option later for batch calls / async calls
    domain: str
    tool_name: str

    arguments: dict[str, Any] = Field(default_factory=dict)
    facts: dict[str, Any] = Field(default_factory=dict)

    message_template: str
    error: str | None = None

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def render(self):
        return self.message_template.format(**self.facts)