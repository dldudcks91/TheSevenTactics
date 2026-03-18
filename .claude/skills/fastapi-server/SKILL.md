---
name: fastapi-server
description: "FastAPI 서버 개발 가이드. async SQLAlchemy + Redis + 단일 API 게이트웨이 패턴. Manager 클래스 작성, DB 세션 관리, Redis 캐싱, 인증(세션), 에러 코드 체계 설계 시 사용."
---

# FastAPI Server 개발 가이드

## 아키텍처 원칙

### 단일 게이트웨이 패턴
- 모든 요청은 `POST /api` → `ApiRequest(api_code, data)`
- `Authorization: Bearer {session_id}` 헤더로 인증
- api_code로 Manager.method 라우팅 (APIManager.api_map)
- 새 기능 = Manager 메서드 작성 + api_map 등록, 그 외 변경 없음

### 데이터 3계층
| 계층 | 저장소 | 용도 | 특성 |
|------|--------|------|------|
| 메타데이터 | CSV → 메모리 | 장비/몬스터/드롭 테이블 | read-only, 서버 기동 시 로드 |
| 유저 데이터 | MySQL (SQLAlchemy) | 계정, 인벤토리, 진행도 | 영구 저장, ORM 관리 |
| 캐시/임시 | Redis | 세션, 전투 스탯, 방치형 타이머 | 휘발성, 장비 변경 시 갱신 |

### 파일 구조 (핵심)
```
fastapi/
├── main.py               # 게이트웨이, 세션 검증, Rate Limiting
├── config.py             # pydantic-settings 환경 변수 (settings.XXX)
├── logger.py             # 전역 로거 (from logger import logger)
├── database.py           # SQLAlchemy 엔진 + 커넥션 풀
├── schemas.py            # ApiRequest (api_code + data)
├── models.py             # ORM 모델 (User, UserStat, Inventory)
└── services/
    ├── system/
    │   ├── APIManager.py       # api_code → Manager 매핑
    │   ├── GameDataManager.py  # CSV 메타데이터 로드
    │   ├── SessionManager.py   # 세션 생성/검증/삭제
    │   └── ErrorCode.py        # 에러 코드 Enum + error_response()
    ├── rpg/
    │   ├── BattleManager.py
    │   ├── InventoryManager.py
    │   └── ItemDropManager.py
    ├── db_manager/
    │   └── DBManager.py
    └── redis_manager/
        └── RedisManager.py     # 비동기 Redis 싱글톤
```

---

## 인증 패턴

### 요청 구조
```
POST /api
Authorization: Bearer {session_id}      ← 세션 헤더
Content-Type: application/json

{"api_code": 3001, "data": {"stage_id": "ch1_01"}}
```
- `user_no`는 클라이언트가 보내지 않음 — 서버가 세션에서 조회
- `main.py`가 세션 → user_no 변환 후 Manager에 전달

### PUBLIC API (세션 불필요)
```python
# main.py
PUBLIC_API_CODES = {
    1002,   # 게임 config 로드
    1003,   # 유저 생성/로그인 (세션 발급)
}
```

### 세션 발급 (로그인 Manager에서)
```python
from services.system.SessionManager import SessionManager

session_id = await SessionManager.create_session(user_no)
return {"success": True, "message": "로그인 완료", "data": {"session_id": session_id}}
```

---

## 에러 코드 체계

### 형식: `E + 4자리` (api_code 4자리 정수와 구분)
```
E1xxx — 시스템/인증   E1001 알 수 없는 API | E1002 인증 실패 | E1003 권한 없음
E2xxx — 유저          E2001 유저 없음       | E2002 이미 존재
E3xxx — 인벤토리      E3001 아이템 없음     | E3002 장착 불가
E4xxx — 전투          E4001 스테이지 없음   | E4002 잘못된 전투 요청
E9xxx — 서버 내부     E9001 DB 오류         | E9002 Redis 오류 | E9999 알 수 없는 오류
```

### 사용법
```python
from services.system.ErrorCode import ErrorCode, error_response

# 에러 반환
return error_response(ErrorCode.USER_NOT_FOUND, "유저를 찾을 수 없습니다.")
# → {"success": False, "error_code": "E2001", "message": "유저를 찾을 수 없습니다."}

# 성공 반환 (기존과 동일)
return {"success": True, "message": "완료", "data": {...}}
```

---

## Manager 클래스 작성 규칙

### 시그니처
```python
from services.system.ErrorCode import ErrorCode, error_response
from logger import logger

class SomeManager:
    @classmethod
    async def some_method(cls, user_no: int, data: dict):
        # 성공
        return {"success": True, "message": "완료", "data": {...}}

        # 에러
        return error_response(ErrorCode.USER_NOT_FOUND, "유저를 찾을 수 없습니다.")
```

### 필수 패턴
- 모든 메서드는 `async` + `@classmethod`
- 성공: `{"success": True, "message": str, "data": ...}`
- 에러: `error_response(ErrorCode.XXX, "설명")` 사용
- 메타데이터 참조: `GameDataManager.REQUIRE_CONFIGS`에서만
- 로깅: `from logger import logger` 후 `logger.info/warning/error`

### API 코드 등록
```python
# APIManager.py의 api_map에 추가
api_map = {
    1001: (SomeManager, "some_method"),
    # 1xxx: 시스템, 2xxx: 인벤토리, 3xxx: 전투
}
```

---

## Redis 패턴

### RedisManager 사용
```python
from services.redis_manager.RedisManager import RedisManager, RedisUnavailable

# 캐시 저장
await RedisManager.setex(key, ttl_seconds, value)

# 캐시 조회
value = await RedisManager.get(key)

# 해시 저장/조회
await RedisManager.hmset(key, {"atk": "150", "def": "80"})
stats = await RedisManager.hgetall(key)
```

### Redis 장애 대응 (필수)
```python
# 캐시가 없어도 서비스 유지 가능한 경우 → DB 폴백
try:
    stats = await RedisManager.hgetall(f"user:{user_no}:battle_stats")
    if not stats:
        raise RedisUnavailable("캐시 miss")
except RedisUnavailable:
    stats = await cls._calc_from_db(user_no)  # DB에서 재계산

# 캐시 없으면 서비스 불가 (세션 등) → RedisUnavailable 위로 전파
# main.py에서 503으로 처리됨
```

### 캐시 키 네이밍
```
session:{session_id}              # 세션 (TTL: 7일)
user:{user_no}:battle_stats       # 전투 스탯 캐시
user:{user_no}:stage_progress     # 스테이지 진행
```

### 무효화 규칙
- 장비 장착/해제 → `user:{user_no}:battle_stats` 삭제

---

## DB 패턴

### SQLAlchemy 세션 (동기)
```python
from database import SessionLocal

db = SessionLocal()
try:
    user = db.query(User).filter(User.user_no == user_no).first()
    db.commit()
finally:
    db.close()
```

### 주의사항
- N+1 쿼리 방지: 필요 시 `joinedload` 활용
- 트랜잭션 단위 명확히 (전투 결과 저장 + 드롭 생성은 하나의 트랜잭션)

---

## 환경 변수 / 설정

```python
from config import settings

settings.DB_HOST
settings.SESSION_TTL_SECONDS   # 604800 (7일)
settings.RATE_LIMIT_DEFAULT    # "30/second"
settings.ENV                   # "development" / "production"
```

`.env` 파일로 관리 (git 제외). `.env.example` 참고.

---

## 로깅

```python
from logger import logger

logger.debug("전투 계산 중간값: ...")    # 개발 시만
logger.info("API 요청/응답, 로그인")
logger.warning("유효하지 않은 요청, 캐시 miss")
logger.error("DB/Redis 오류", exc_info=True)
```
- 콘솔: INFO 이상
- 파일 (`logs/rpg_server.log`): WARNING 이상, 7일 보관

---

## 성능 체크리스트

- [ ] 무거운 연산은 `asyncio.to_thread()`로 분리
- [ ] DB 쿼리 수 확인 (API 1건당 3개 이하 목표)
- [ ] Redis 장애 시 폴백 로직 있는지 확인
- [ ] 응답 시간 100ms 이하 목표
- [ ] CSV 메타데이터는 절대 런타임에 파일 I/O 금지 (메모리 참조만)
