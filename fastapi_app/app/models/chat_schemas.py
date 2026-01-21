from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict, Any


class ModelResponseDataListPermission(BaseModel):
    id: str
    object: str = "model_permission"
    created: int
    allow_create_engine: bool
    allow_sampling: bool
    allow_logprobs: bool
    allow_search_indices: bool
    allow_view: bool
    allow_fine_tuning: bool
    organization: str
    group: Optional[str] = None
    is_blocking: bool

class ModelResponseData(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str
    root: str
    parent: Optional[str] = None
    max_model_len: int
    permission: List[ModelResponseDataListPermission]

class ModelResponse(BaseModel):
    object: str
    data: List[ModelResponseData]

class ChatMessage(BaseModel):
    role: str = Field(..., description="system, user, assistant 중 하나")
    content: str = Field(..., description="메시지 내용")

class ToolDefinition(BaseModel):
    object: str
    data: List[ModelResponseData]

class ChatCompletionsRequest(BaseModel):
    model: str = Field(..., example="openai/gpt-oss-20b")
    messages: List[ChatMessage]
    stream: Optional[bool] = False
    tools: Optional[List[ToolDefinition]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None

