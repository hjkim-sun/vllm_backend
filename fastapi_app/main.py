from fastapi_app.app.api.v1.vllm_endpoint import router as vllm_router
from fastapi import FastAPI
from fastapi_app.app.core.config import settings
from fastapi_app.app.utils.logger import setup_logging

# env 변수 로드
setup_logging()

# FastAPI 시작
app = FastAPI()
app.include_router(vllm_router, tags=["vllm"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)