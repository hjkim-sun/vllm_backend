from fastapi_app.app.models.chat_schemas import ChatCompletionsRequest
from fastapi.responses import StreamingResponse
from fastapi_app.app.utils.logger import get_logger
from fastapi_app.app.core.config import settings
from tools.realtime_weather_api_tool.weather_api_tool import WeatherApiTool
from tools.tool_executor import ToolExecutor
from typing import AsyncGenerator
from fastapi import HTTPException
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

        # vLLM에 요청할 payload 에 툴 목록 추가 
        weather_api_tool = WeatherApiTool()
        self.tool_call_functions = {"get_weather_api": weather_api_tool.get_weather_api}
        
        request_json["tools"] = [weather_api_tool.tools_description]
        request_json["tool_choice"] = "auto"
        self.log.info(f"chat_completions Request body: {request_json}")
        tool_executor = ToolExecutor()

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
                                    # yield f"{line}\n\n"
                                    
                                    # OpenWebUI는 툴 콜과 관련한 모델의 응답을 받으면 내부적으로 툴 실행을 시도하므로 parsing_tool_message 함수 내에서 해당 청크는 미전송하도록 구성
                                    chunk = tool_executor.parsing_tool_message(line)
                                    if chunk:
                                        if tool_executor.is_tool_call and chunk.startswith("data: [DONE]"):  # 모델의 응답이 툴콜일 경우 대화가 종료되지 않도록 끝 청크는 미전송
                                            break
                                        else:
                                            yield chunk

                                        
                            # 툴 함수를 실행하고 결과를 담아 모델로 재요청
                            if tool_executor.is_tool_call:
                                run_tool_rslts = await tool_executor.run_tool_function(self.tool_call_functions)
                                messages = tool_executor.rebuild_messages(messages=request_json["messages"], tool_rslts=run_tool_rslts)

                                # # messages 교체
                                request_json["messages"] = messages
                                self.log.info(request_json)
                                async with client.stream("POST", url=self.url_v1_chat_completions, json=request_json, headers=self.headers) as response:
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
        

    