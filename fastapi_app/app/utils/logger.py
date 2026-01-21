import logging
from pathlib import Path

def setup_logging():
    base_dir = Path(__file__).resolve().parent.parent.parent
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "service.log"

    # 전체 로깅 설정 (main.py에서 실행될 예정)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger("AppInitializer")
    logger.info("Logging system initialized.")

def get_logger(name: str):
    return logging.getLogger(name)