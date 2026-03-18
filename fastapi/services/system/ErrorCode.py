from enum import Enum


class ErrorCode(str, Enum):
    """
    에러 코드 체계 — E + 4자리
    api_code(4자리 정수)와 자릿수+접두사로 명확히 구분

    E1xxx — 시스템/인증
    E2xxx — 유저
    E3xxx — 인벤토리
    E4xxx — 전투
    E9xxx — 서버 내부
    """

    # ── E1xxx: 시스템/인증 ──────────────────────────────
    UNKNOWN_API_CODE    = "E1001"   # 등록되지 않은 api_code
    AUTH_FAILED         = "E1002"   # 세션 없음 또는 만료
    FORBIDDEN           = "E1003"   # 권한 없음

    # ── E1xxx 추가 ────────────────────────────────────────
    INVALID_REQUEST     = "E1004"   # 잘못된 요청 (범용)

    # ── E2xxx: 유저 ─────────────────────────────────────
    USER_NOT_FOUND      = "E2001"   # 유저 없음
    USER_ALREADY_EXISTS = "E2002"   # 이미 존재하는 유저
    INVALID_PASSWORD    = "E2003"   # 비밀번호 불일치 또는 형식 오류

    # ── E3xxx: 인벤토리 ──────────────────────────────────
    ITEM_NOT_FOUND      = "E3001"   # 아이템 없음
    EQUIP_SLOT_MISMATCH = "E3002"   # 장착 불가 (부위 불일치)
    COST_EXCEEDED       = "E3003"   # 코스트 초과
    INVENTORY_FULL      = "E3004"   # 인벤토리 가득 참
    COLLECTION_NOT_FOUND  = "E3005"  # 도감 항목 없음
    SKILL_SLOT_INVALID    = "E3006" # 스킬 슬롯 오류 (미해금/이미 사용 중)
    ENHANCE_FAILED      = "E3007"   # 강화 실패 (최대 레벨 등)
    INSUFFICIENT_GOLD   = "E3008"   # 골드 부족

    # ── E4xxx: 전투 ──────────────────────────────────────
    STAGE_NOT_FOUND     = "E4001"   # 스테이지 없음
    INVALID_BATTLE_REQ  = "E4002"   # 잘못된 전투 요청
    STAGE_NOT_UNLOCKED  = "E4003"   # 스테이지 미해금

    # ── E9xxx: 서버 내부 ─────────────────────────────────
    DB_ERROR            = "E9001"   # DB 오류
    REDIS_ERROR         = "E9002"   # Redis 오류
    INTERNAL_ERROR      = "E9999"   # 알 수 없는 서버 오류


def error_response(code: ErrorCode, message: str) -> dict:
    """에러 응답 딕셔너리 생성 헬퍼"""
    return {
        "success": False,
        "error_code": code.value,
        "message": message,
    }
