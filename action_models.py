from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class ActionOutcome(BaseModel):
    status: Literal["success", "failed", "declined"]
    domain: str
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    facts: dict[str, Any] = Field(default_factory=dict)
    message_template: str
    error: str | None = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def render(self) -> str:
        return self.message_template.format(**self.facts)


class ActionKernel:
    def __init__(self, tool_registry, state_manager):
        self.tool_registry = tool_registry
        self.state_manager = state_manager

    def execute(
        self,
        domain: str,
        tool_name: str,
        arguments: dict,
    ) -> ActionOutcome:
        try:
            tool = self.tool_registry[domain][tool_name]
        except KeyError as error:
            raise LookupError(f"Unknown tool: {domain}.{tool_name}") from error

        validated = tool.args_model.model_validate(arguments).model_dump()

        try:
            outcome = tool.handler(**validated)
        except Exception as error:
            outcome = tool_error(
                domain=domain,
                tool_name=tool_name,
                arguments=validated,
                error=f"{type(error).__name__}: {error}",
            )

        if not isinstance(outcome, ActionOutcome):
            outcome = tool_error(
                domain=domain,
                tool_name=tool_name,
                arguments=validated,
                error=(
                    f"Tool contract violation: {domain}.{tool_name} returned "
                    f"{type(outcome).__name__}, expected ActionOutcome."
                ),
            )

        self.state_manager.record_outcome(outcome)
        if outcome.status == "success":
            self.state_manager.apply(outcome)

        return outcome


def tool_error(
    domain: str,
    tool_name: str,
    error: str,
    arguments: dict | None = None,
    facts: dict | None = None,
    message_template: str = "I couldn't complete that action.",
) -> ActionOutcome:
    return ActionOutcome(
        status="failed",
        domain=domain,
        tool_name=tool_name,
        arguments=arguments or {},
        facts=facts or {},
        message_template=message_template,
        error=error,
    )


def tool_success(
    domain: str,
    tool_name: str,
    arguments: dict | None = None,
    facts: dict | None = None,
    message_template: str = "I successfully executed the action.",
) -> ActionOutcome:
    return ActionOutcome(
        status="success",
        domain=domain,
        tool_name=tool_name,
        arguments=arguments or {},
        facts=facts or {},
        message_template=message_template,
    )
