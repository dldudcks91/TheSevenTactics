import uuid
from typing import Optional
from config import settings
from services.redis_manager.RedisManager import RedisManager, RedisUnavailable


# Redis 세션 키 형식: session:{session_id} → user_no (str)
SESSION_PREFIX = "session:"


class SessionManager:
    """세션 생성 / 검증 / 삭제 관리자"""

    @classmethod
    async def create_session(cls, user_no: int) -> str:
        """
        로그인 성공 시 세션 생성
        반환: session_id (클라이언트에게 전달)
        RedisUnavailable 발생 시 호출부에서 처리
        """
        session_id = str(uuid.uuid4())
        key = SESSION_PREFIX + session_id
        await RedisManager.setex(key, settings.SESSION_TTL_SECONDS, str(user_no))
        return session_id

    @classmethod
    async def get_user_no(cls, session_id: str) -> Optional[int]:
        """
        Authorization 헤더의 세션 검증
        반환: user_no (유효) / None (세션 없음 또는 만료)
        RedisUnavailable 발생 시 호출부에서 처리
        """
        if not session_id:
            return None
        key = SESSION_PREFIX + session_id
        value = await RedisManager.get(key)
        if value is None:
            return None
        return int(value)

    @classmethod
    async def delete_session(cls, session_id: str):
        """로그아웃 시 세션 삭제 — Redis 오류 시 조용히 무시 (이미 끊긴 세션)"""
        try:
            key = SESSION_PREFIX + session_id
            await RedisManager.delete(key)
        except RedisUnavailable:
            pass
