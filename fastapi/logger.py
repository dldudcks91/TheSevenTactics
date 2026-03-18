import logging
import logging.handlers
import os


LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "rpg_server.log")
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger() -> logging.Logger:
    """
    RPG_SERVER 로거 설정
    - 콘솔: INFO 이상 출력
    - 파일:  WARNING 이상, 하루 단위 로테이션, 7일 보관
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("RPG_SERVER")
    logger.setLevel(logging.DEBUG)  # 루트 레벨은 DEBUG — 핸들러가 필터링

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # 콘솔 핸들러 — INFO 이상
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 파일 핸들러 — WARNING 이상, 자정에 롤오버, 7일 보관
    file_handler = logging.handlers.TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# 전역 싱글톤 — 전체 앱에서 from logger import logger 로 참조
logger = setup_logger()
