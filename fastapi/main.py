from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from schemas import ApiRequest
import database

from config import settings
from logger import logger
from services.system import GameDataManager, APIManager
from services.system.ErrorCode import ErrorCode, error_response
from services.system.SessionManager import SessionManager
from services.redis_manager.RedisManager import RedisManager, RedisUnavailable


# ── Rate Limiter 설정 ────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="TheSevenTactics Server")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# 세션 없이 접근 가능한 API 코드 목록
PUBLIC_API_CODES = {
    1002,   # 게임 config 로드 (로그인 전 필요)
    1003,   # 회원가입 (세션 발급)
    1007,   # 로그인 (세션 발급)
}


# ── 서버 시작/종료 ───────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info("=== TheSevenTactics Server Starting Up ===")
    await RedisManager.init()
    GameDataManager.load_all_csv(base_path="./meta_data/")
    database.init_db()
    logger.info("=== TheSevenTactics Server Ready ===")


@app.on_event("shutdown")
async def shutdown_event():
    await RedisManager.close()
    logger.info("=== TheSevenTactics Server Shutdown ===")


# ── 헬스체크 ─────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """로드밸런서/컨테이너 헬스체크 — Redis 상태 포함"""
    redis_ok = await RedisManager.ping()
    status = "ok" if redis_ok else "degraded"  # Redis 다운 시 degraded (서버는 살아있음)

    if not redis_ok:
        logger.warning("[HEALTH] Redis 연결 불가")

    return {
        "status": status,
        "env": settings.ENV,
        "redis": "ok" if redis_ok else "unavailable",
    }


# ── API 게이트웨이 ────────────────────────────────────────────

@app.post("/api")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def api_gateway(request: Request, body: ApiRequest):
    """모든 클라이언트 요청이 들어오는 유일한 관문"""

    api_code = body.api_code

    # 1. 등록되지 않은 api_code 확인
    if api_code not in APIManager.api_map:
        logger.warning(f"[API] 알 수 없는 api_code={api_code}")
        return JSONResponse(status_code=400, content=error_response(
            ErrorCode.UNKNOWN_API_CODE,
            f"등록되지 않은 API 코드입니다: {api_code}"
        ))

    # 2. 세션 검증 (PUBLIC API는 통과)
    user_no = 0
    if api_code not in PUBLIC_API_CODES:
        session_id = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
        try:
            user_no = await SessionManager.get_user_no(session_id)
        except RedisUnavailable:
            # Redis 다운 → 세션 확인 불가 → 서비스 일시 중단
            logger.error("[AUTH] Redis 장애로 세션 검증 불가")
            return JSONResponse(status_code=503, content=error_response(
                ErrorCode.REDIS_ERROR,
                "서버 점검 중입니다. 잠시 후 다시 시도해주세요."
            ))

        if user_no is None:
            logger.warning(f"[AUTH] 세션 없음 또는 만료 api_code={api_code}")
            return JSONResponse(status_code=401, content=error_response(
                ErrorCode.AUTH_FAILED,
                "인증이 필요합니다. 다시 로그인해주세요."
            ))

    logger.info(f"[API] user={user_no} api_code={api_code}")

    # 3. 매핑된 Manager 메서드 호출
    _, manager_method = APIManager.api_map[api_code]
    try:
        result = await manager_method(user_no, body.data)
        return JSONResponse(content=result)

    except RedisUnavailable:
        # 캐시 miss 이후 DB 재계산 로직이 없는 Manager에서 Redis 오류 발생 시
        logger.error(f"[API] api_code={api_code} Redis 장애")
        return JSONResponse(status_code=503, content=error_response(
            ErrorCode.REDIS_ERROR,
            "서버 점검 중입니다. 잠시 후 다시 시도해주세요."
        ))
    except Exception as e:
        logger.error(f"[API] api_code={api_code} 실행 오류: {e}", exc_info=True)
        return JSONResponse(status_code=500, content=error_response(
            ErrorCode.INTERNAL_ERROR,
            "서버 내부 오류가 발생했습니다."
        ))
# Static mount를 파일 맨 끝으로 이동
app.mount("/", StaticFiles(directory="public", html=True), name="public")
