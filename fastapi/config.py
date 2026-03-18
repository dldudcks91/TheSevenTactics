from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # DB 설정
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str
    DB_NAME: str = "TheSevenTactics"
    DB_CHARSET: str = "utf8"

    # DB 커넥션 풀 설정
    DB_POOL_SIZE: int = 5          # 기본 유지 커넥션 수
    DB_MAX_OVERFLOW: int = 10      # 풀 초과 시 추가 허용 커넥션 수 (최대 15개)
    DB_POOL_TIMEOUT: int = 30      # 커넥션 대기 최대 시간 (초)
    DB_POOL_RECYCLE: int = 3600    # 커넥션 재생성 주기 (초) — MySQL 8시간 타임아웃 방지

    # Redis 설정
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # 세션 설정
    SESSION_TTL_SECONDS: int = 604800   # 7일 (7 * 24 * 60 * 60)

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "30/second"   # 전체 API — IP당
    RATE_LIMIT_LOGIN: str = "5/minute"      # 로그인 API — 브루트포스 방어

    # 서버 설정
    ENV: str = "development"       # development / production

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )


# 전역 싱글톤 — 전체 앱에서 settings.DB_HOST 형태로 참조
settings = Settings()
