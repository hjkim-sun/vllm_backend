from fastapi_app.app.models.chat_schemas import ChatCompletionsRequest
from fastapi.responses import StreamingResponse
from fastapi_app.app.utils.logger import get_logger
from fastapi_app.app.core.config import settings
from typing import AsyncGenerator
from fastapi import HTTPException
import os
import httpx

logger = get_logger(__name__)

class VllmCompletions():
    def __init__(self):
        self.log = logger
        self.vllm_ip_port = settings.VLLM_IP_PORT.rstrip("/")
        self.vllm_api_key = settings.VLLM_API_KEY
        self.httpx_timeout = 120
        self.url_v1_model = f"{self.vllm_ip_port}/v1/models"
        self.url_v1_chat_completions = f"{self.vllm_ip_port}/v1/chat/completions"
        self.headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.vllm_api_key}"}

    async def chat_completions(self, request: ChatCompletionsRequest):
        request_json = request.model_dump()
        self.log.info(f"chat_completions Request body: {request_json}")
        is_stream = request.stream

        # SSE 요청인 경우
        if is_stream:
            async def event_stream() -> AsyncGenerator[str, None]:
                try:
                    async with httpx.AsyncClient(timeout=self.httpx_timeout) as client:
                        async with client.stream("POST", url=self.url_v1_chat_completions, json=request_json, headers=self.headers) as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if line:
                                    self.log.debug(line)
                                    yield f"{line}\n\n"

                except httpx.ReadTimeout as e:
                    self.log.error(f"vLLM streaming timeout: {e}")
                    yield "event: error\ndata: {\"error\": \"vLLM request timeout\"}\n\n"


            return StreamingResponse(event_stream(), media_type="text/event-stream")

        # 정적 요청인 경우
        else:
            try:
                async with httpx.AsyncClient(timeout=self.httpx_timeout) as client:
                    response = await client.post(self.url_v1_chat_completions, json=request.model_dump(), headers=self.headers)
                    self.log.info(f"Static response: {response.json()}")
                    resp = response.json()
                    return resp
            except httpx.ReadTimeout as e:
                self.log.error(f"vLLM timeout: {e}")
                raise HTTPException(
                    status_code=502,
                    detail="vLLM request timeout"
                )


    async def get_models(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url_v1_model, headers=self.headers)
            return response.json()