import uuid
from typing import Any

from pydantic import BaseModel, Field


class AgentAskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: uuid.UUID | None = None


class AgentStepEvent(BaseModel):
    type: str
    content: str
    iteration: int


class AgentUsageSummary(BaseModel):
    model: str | None = None
    iterations: int = 0
    llm_calls: int = 0
    tool_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    events: list[dict[str, Any]] = Field(default_factory=list)


class AgentFinalEvent(BaseModel):
    answer: str
    iterations: int
    steps: list[AgentStepEvent]
    session_id: uuid.UUID | None = None
    usage: AgentUsageSummary | None = None
