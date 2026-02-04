from fastapi import APIRouter
from fastapi_app.app.models.chat_schemas import ChatCompletionsRequest
from fastapi_app.app.models.chat_schemas import ModelResponse
from fastapi_app.app.services.chat_service import VllmCompletions

router = APIRouter()
vllm_completions = VllmCompletions()

@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionsRequest):
    result = await vllm_completions.chat_completions(request)
    return result

@router.get("/v1/models", response_model=ModelResponse)
async def get_models():
    result = await vllm_completions.get_models()
    return result