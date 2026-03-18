import redis.asyncio as aioredis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
from config import settings


class RedisUnavailable(Exception):
    """Redis 연결 불가 시 발생 — 호출부에서 폴백 처리"""
    pass


class RedisManager:
    """Redis 비동기 클라이언트 — 클래스 변수로 싱글톤 관리"""

    _client: aioredis.Redis = None

    # ── 연결 관리 ────────────────────────────────────────────

    @classmethod
    async def init(cls):
        """서버 startup 시 호출 — Redis 연결 초기화"""
        cls._client = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=3,   # 연결 시도 최대 3초
            socket_timeout=3,           # 명령 응답 최대 3초
        )

    @classmethod
    async def close(cls):
        """서버 shutdown 시 호출 — Redis 연결 종료"""
        if cls._client:
            await cls._client.aclose()

    @classmethod
    async def ping(cls) -> bool:
        """Redis 연결 상태 확인 — health check 용"""
        try:
            return await cls._client.ping()
        except (RedisError, RedisConnectionError, Exception):
            return False

    # ── 내부 에러 래퍼 ───────────────────────────────────────

    @classmethod
    async def _exec(cls, coro):
        """
        모든 Redis 명령을 감싸는 에러 래퍼.
        연결 오류 → RedisUnavailable 발생 (호출부에서 폴백 처리)
        """
        try:
            return await coro
        except (RedisConnectionError, RedisError) as e:
            raise RedisUnavailable(f"Redis 명령 실패: {e}") from e

    # ── String ───────────────────────────────────────────────

    @classmethod
    async def get(cls, key: str):
        return await cls._exec(cls._client.get(key))

    @classmethod
    async def setex(cls, key: str, seconds: int, value: str):
        return await cls._exec(cls._client.setex(key, seconds, value))

    @classmethod
    async def delete(cls, *keys: str):
        return await cls._exec(cls._client.delete(*keys))

    @classmethod
    async def expire(cls, key: str, seconds: int):
        return await cls._exec(cls._client.expire(key, seconds))

    @classmethod
    async def incr(cls, key: str) -> int:
        return await cls._exec(cls._client.incr(key))

    # ── Hash ─────────────────────────────────────────────────

    @classmethod
    async def hset(cls, key: str, field: str, value: str):
        return await cls._exec(cls._client.hset(key, field, value))

    @classmethod
    async def hmset(cls, key: str, mapping: dict):
        return await cls._exec(cls._client.hset(key, mapping=mapping))

    @classmethod
    async def hgetall(cls, key: str) -> dict:
        return await cls._exec(cls._client.hgetall(key))

    @classmethod
    async def hdel(cls, key: str, *fields: str):
        return await cls._exec(cls._client.hdel(key, *fields))

    # ── Sorted Set ───────────────────────────────────────────

    @classmethod
    async def zadd(cls, key: str, mapping: dict):
        return await cls._exec(cls._client.zadd(key, mapping))

    @classmethod
    async def zrangebyscore(cls, key: str, min_score, max_score):
        return await cls._exec(cls._client.zrangebyscore(key, min_score, max_score))

    @classmethod
    async def zrem(cls, key: str, *members: str):
        return await cls._exec(cls._client.zrem(key, *members))

    # ── 유틸 ─────────────────────────────────────────────────

    @classmethod
    async def keys(cls, pattern: str):
        return await cls._exec(cls._client.keys(pattern))
