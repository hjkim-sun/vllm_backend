import inspect
import asyncio
import json
from fastapi_app.app.utils.logger import get_logger

logger = get_logger(__name__)

class ToolExecutor():
    def __init__(self):
        self.tool_calls = {}
        self.is_tool_call = False
        self.log = logger

    def parsing_tool_message(self, line: str) -> bool:  
        '''
        모델이 tool call 응답을 할 때 chunk를 파싱하여 함수명과 arguments를 작성하기 위한 함수 
        Tool call 응답시 chunk의 choices[0]['delta'] 부분은 아래와 같이 옴
        'delta': {'tool_calls': [{'id': 'chatcmpl-tool-799721c2e0014e6ca0b504a9ee735de4', 'type': 'function', 'index': 0, 'function': {'name': 'get_current_weather', 'arguments': ''}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': '{"'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': 'city'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': '":"'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': '강'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': '릉'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': '","'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': 'unit'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': '":"'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': '섭'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': '씨'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {'tool_calls': [{'index': 0, 'function': {'arguments': '"}'}}]}, 'logprobs': None, 'finish_reason': None, 'token_ids': None}]}
        'delta': {}, 'logprobs': None, 'finish_reason': 'tool_calls', 'stop_reason': 200012, 'token_ids': None}]}

        chunk를 파싱하여 self.tool_calls 변수를 아래와 같이 채우기 위한 목적
            0: {
            "id": "chatcmpl-tool-799721c2e0014e6ca0b504a9ee735de4"",
            "name": "get_current_weather",
            "arguments": '{city: "강릉", "unit": "섭씨"}'
        }
        '''

        # 종료 시그널일 경우 
        if line.startswith("data: [DONE]"):
            return f"{line}\n\n"
        
        json_data = json.loads(line[len("data: "):])
        choices = json_data['choices']
        delta = choices[0]["delta"]

        # delta 부분에 tool_calls 키가 없으면 그대로 리턴, OpenWebUI로 전달
        if "tool_calls" not in delta and choices[0]['finish_reason'] is None:
            return f"{line}\n\n"
        
        if delta.get("tool_calls"):
            self.is_tool_call = True

            for tc in delta["tool_calls"]:
                idx = tc["index"]

                if idx not in self.tool_calls:
                    self.tool_calls[idx] = {
                        "id": None,
                        "name": None,
                        "arguments": ""
                    }

                state = self.tool_calls[idx]

                # id 키가 있으면 채우기
                if "id" in tc:
                    state["id"] = tc["id"]

                # function 키가 있으면 채우기
                if "function" in tc:
                    fn = tc["function"]
                    if "name" in fn:
                        state["name"] = fn["name"]

                    # arguments 내용은 chunk 마다 나뉘어서 오므로 concat 필요
                    if "arguments" in fn:
                        state["arguments"] += fn["arguments"]


    async def run_tool_function(self, tool_functions: dict) -> list:
        '''
        작성된 self.tool_calls 변수를 이용해 함수 실행
        '''
        run_tool_rslts = []
        for idx, func_info in self.tool_calls.items():
            func_name = func_info["name"]
            func_args = json.loads(func_info["arguments"])
            self.log.info(f"func_name: {func_name}")
            self.log.info(f"func_args: {func_args}")

            # 툴 실행, 툴이 비동기 함수이면 바로 실행하고 동기 함수면 asyncio.to_thread()를 이용해 비동기 구조로 처리
            function_target = tool_functions[func_name]
            if inspect.iscoroutinefunction(function_target):
                tool_rslt = await function_target(**func_args)
            else:
                tool_rslt = await asyncio.to_thread(function_target, **func_args)
            run_tool_rslts.append(tool_rslt)

            self.log.info(f"Tool function 실행 결과: {tool_rslt}")

        return run_tool_rslts
    

    def rebuild_messages(self, messages: list, tool_rslts: list) -> list:
        assistant_message = {
            "role": "assistant",
            "tool_calls": []
        }

        for idx, tool_call in self.tool_calls.items():
            model_tool_msg = {
                "id": tool_call["id"],
                "type": "function",
                "function": {
                    "name": tool_call["name"],
                    "arguments": tool_call["arguments"]
                }
            }
            assistant_message["tool_calls"].append(model_tool_msg)

        messages.append(assistant_message)
        for idx, tool_rslt in enumerate(tool_rslts):
            tool_message = {
                "role": "tool",
                "tool_call_id": self.tool_calls[idx]["id"],
                "content": tool_rslt
            }

            messages.append(tool_message)
        self.log.info(f"rebuild message: {messages}")
        return messages