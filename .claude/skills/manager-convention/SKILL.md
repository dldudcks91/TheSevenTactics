---
name: manager-convention
description: "Manager 클래스 코딩 컨벤션. 메서드 내부 구조, DB 트랜잭션 패턴, 검증 순서, 에러 처리, Redis 캐시 무효화, 로깅 규칙 등 Manager 코드 작성 시 반드시 따라야 할 코드 레벨 규칙."
---

# Manager 클래스 코딩 컨벤션

Manager 클래스 내부의 메서드를 작성할 때 반드시 따르는 코드 레벨 규칙.
`fastapi-server` skill의 아키텍처 규칙 위에서 동작한다.

---

## 1. 메서드 내부 구조 (실행 순서)

모든 Manager 메서드는 아래 6단계 순서를 따른다.
해당 없는 단계는 생략하되, 순서를 바꾸지 않는다.

```python
@classmethod
async def some_action(cls, user_no: int, data: dict):
    """
    [1] 입력 추출 & 타입 변환
    [2] 메타데이터 검증 (CSV 기반, DB 불필요)
    [3] DB 세션 열기 + 소유권/상태 검증
    [4] 비즈니스 로직 실행
    [5] DB 커밋 + Redis 캐시 무효화
    [6] 응답 반환
    """
```

### 단계별 상세

```python
@classmethod
async def some_action(cls, user_no: int, data: dict):
    # ── [1] 입력 추출 ──
    # data에서 필요한 값을 꺼내고 타입 변환
    # 누락 시 즉시 error_response 반환 (DB 열기 전에 차단)
    item_uid = data.get("item_uid")
    if not item_uid:
        return error_response(ErrorCode.INVALID_REQUEST, "item_uid 필요")

    # ── [2] 메타데이터 검증 ──
    # GameDataManager.REQUIRE_CONFIGS에서 유효성 확인
    # DB 접근 없이 판단 가능한 검증은 여기서 처리
    config = GameDataManager.REQUIRE_CONFIGS.get("some_config")
    if not config:
        return error_response(ErrorCode.INTERNAL_ERROR, "설정 미로드")

    # ── [3] DB 세션 + 소유권/상태 검증 ──
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_no == user_no).first()
        if not user:
            return error_response(ErrorCode.USER_NOT_FOUND, "유저 없음")

        item = db.query(Item).filter(
            Item.item_uid == item_uid,
            Item.user_no == user_no        # 소유권 검증 필수
        ).first()
        if not item:
            return error_response(ErrorCode.ITEM_NOT_FOUND, "아이템 없음")

        # 상태 검증: 현재 상태에서 이 동작이 가능한지
        if item.equip_slot is not None:
            return error_response(ErrorCode.INVALID_REQUEST, "장착 중인 아이템")

        # ── [4] 비즈니스 로직 ──
        # 계산, 상태 변경, 관련 레코드 생성/삭제
        user.gold -= cost
        item.item_level += 1

        # ── [5] 커밋 + 캐시 무효화 ──
        db.commit()

        # 커밋 성공 후에만 캐시 무효화 (커밋 전에 하면 안 됨)
        await cls._invalidate_cache(user_no, item)

    except Exception as e:
        db.rollback()
        logger.error(f"[SomeManager] some_action 실패: {e}", exc_info=True)
        return error_response(ErrorCode.DB_ERROR, "처리 중 오류")
    finally:
        db.close()

    # ── [6] 응답 반환 ──
    # try 블록 밖에서 반환 (DB 세션이 닫힌 후)
    return {
        "success": True,
        "message": "처리 완료",
        "data": {"item_uid": item_uid, "new_level": item.item_level}
    }
```

---

## 2. DB 트랜잭션 규칙

### 세션 생명주기
```python
db = SessionLocal()
try:
    # 모든 DB 작업
    db.commit()          # 성공 시 한 번만
except Exception:
    db.rollback()        # 실패 시 롤백
finally:
    db.close()           # 항상 닫기
```

### 원칙
- **하나의 메서드 = 하나의 트랜잭션**: 메서드 내에서 commit은 1회만
- **조기 반환 시 commit 하지 않음**: 검증 실패 → error_response 반환 시 commit 없이 finally로 직행
- **flush 사용**: auto-increment 값이 필요할 때만 `db.flush()` 사용 (commit 전 ID 확보)
- **읽기 전용 메서드**: commit 불필요, try/finally만 사용

### 금지사항
- 하나의 메서드에서 여러 번 commit 금지 (부분 커밋 방지)
- Manager 간 DB 세션 공유 금지 (각 메서드가 자체 세션 관리)
- commit 후 같은 세션으로 추가 쿼리 금지

---

## 3. 검증 순서 (Validation Chain)

검증은 비용이 낮은 것부터 높은 순서로 진행한다.

```
[1] 입력값 존재/타입 검증     ← DB 없이 가능, 가장 먼저
[2] 메타데이터 유효성          ← 메모리 조회만
[3] 소유권 검증 (user_no)     ← DB 필요
[4] 상태 검증                  ← DB 필요 (장착 여부, 레벨 등)
[5] 자원 검증 (골드, 슬롯)    ← DB 필요 (부족 시 차단)
```

### 소유권 검증 필수 항목
- **아이템**: `Item.user_no == user_no`
- **카드**: `Card.user_no == user_no`
- **스테이지**: `stage_id <= user.current_stage`
- 클라이언트가 보낸 ID로 다른 유저의 데이터에 접근하지 못하도록 항상 user_no 조건 포함

---

## 4. 에러 처리 패턴

### 비즈니스 에러 vs 시스템 에러

```python
# 비즈니스 에러: 유저 행동이 잘못된 경우 → error_response + 적절한 ErrorCode
if user.gold < cost:
    return error_response(ErrorCode.INSUFFICIENT_GOLD, "골드 부족")

# 시스템 에러: 예상치 못한 오류 → except 블록에서 처리
except Exception as e:
    db.rollback()
    logger.error(f"[ManagerName] method_name 실패: {e}", exc_info=True)
    return error_response(ErrorCode.DB_ERROR, "처리 중 오류")
```

### 규칙
- 비즈니스 에러는 `except`에 넣지 않는다 (정상 흐름의 분기)
- 시스템 에러의 `except`는 반드시 `logger.error` + `exc_info=True` 포함
- 에러 메시지에 내부 구현 상세를 노출하지 않는다 (유저에게는 간결한 메시지)
- `except Exception`은 최후의 방어선 — 예측 가능한 에러는 구체적 타입으로 잡는다

---

## 5. Redis 캐시 무효화 규칙

### 무효화 타이밍
```python
# 반드시 DB commit 성공 후에 캐시 무효화
db.commit()

# 캐시 무효화 (실패해도 서비스 중단 안 됨)
try:
    await RedisManager.delete(f"user:{user_no}:battle_stats")
except RedisUnavailable:
    logger.warning(f"[ManagerName] 캐시 무효화 실패 (user_no={user_no})")
```

### 무효화 트리거 매핑
| 변경 사항 | 무효화 대상 키 |
|-----------|----------------|
| 장비 장착/해제 | `user:{user_no}:battle_stats` |
| 카드 장착/해제 (장착된 장비에) | `user:{user_no}:battle_stats` |
| 아이템 강화 (장착된 장비) | `user:{user_no}:battle_stats` |
| 아이템 판매 (장착된 장비) | `user:{user_no}:battle_stats` |
| 레벨업 (스탯 변경) | `user:{user_no}:battle_stats` |

### 캐시 무효화 조건 분기
```python
# 장착 중인 아이템이 변경된 경우에만 전투 스탯 캐시 무효화
if item.equip_slot is not None:
    try:
        await RedisManager.delete(f"user:{user_no}:battle_stats")
    except RedisUnavailable:
        pass  # 다음 전투 시 DB에서 재계산됨
```

---

## 6. 로깅 컨벤션

### 포맷
```python
logger.info(f"[ManagerName] 동작 설명 (user_no={user_no}, key=value)")
logger.error(f"[ManagerName] method_name 실패: {e}", exc_info=True)
```

### 레벨 사용 기준
| 레벨 | 용도 | 예시 |
|------|------|------|
| `debug` | 계산 중간값, 개발 추적용 | 전투 시뮬레이션 턴별 데미지 |
| `info` | 주요 비즈니스 이벤트 | 유저 생성, 장비 장착, 레벨업 |
| `warning` | 비정상이지만 서비스 가능 | 캐시 miss, Redis 장애 폴백 |
| `error` | 서비스 실패, 데이터 정합성 위험 | DB 커밋 실패, 예외 발생 |

### 규칙
- `[ManagerName]` 접두사 필수 (로그 추적용)
- 민감 정보 (비밀번호, 세션ID 전체) 로깅 금지
- `error` 레벨은 반드시 `exc_info=True` 포함

---

## 7. 응답 구성 규칙

### 성공 응답
```python
return {
    "success": True,
    "message": "처리 완료",        # 간결한 한글 설명
    "data": {                       # 클라이언트가 필요한 최소 데이터
        "item_uid": 123,
        "new_level": 5
    }
}
```

### 에러 응답
```python
return error_response(ErrorCode.INSUFFICIENT_GOLD, "골드가 부족합니다.")
# → {"success": False, "error_code": "E3008", "message": "골드가 부족합니다."}
```

### 규칙
- 성공 응답에 `error_code` 포함하지 않음
- 에러 응답에 반드시 `error_response()` 사용 (직접 dict 생성 금지)
- `data`에는 클라이언트 UI 갱신에 필요한 값만 포함
- DB 모델 객체를 그대로 반환하지 않음 (필요한 필드만 추출)

---

## 8. 헬퍼 메서드 규칙

### private 메서드 네이밍
```python
class BattleManager:
    @classmethod
    async def battle_result(cls, user_no, data):     # public: API 진입점
        ...

    @classmethod
    async def _load_battle_stats(cls, user_no):       # private: 내부 전용
        ...

    @classmethod
    def _calculate_damage(cls, atk, defense):         # private + 동기: 순수 계산
        ...
```

### 규칙
- API 진입점 메서드: `snake_case` (api_map에 등록)
- 내부 헬퍼: `_underscore_prefix`
- 순수 계산 함수: `async` 불필요 시 동기 메서드로 작성
- 헬퍼가 DB 세션을 받아야 하면 파라미터로 전달 (자체 세션 생성 금지)

### DB 세션 전달 패턴
```python
@classmethod
async def main_action(cls, user_no, data):
    db = SessionLocal()
    try:
        # 헬퍼에 db 전달
        result = cls._validate_and_calc(db, user_no, item_uid)
        db.commit()
    finally:
        db.close()

@classmethod
def _validate_and_calc(cls, db, user_no, item_uid):
    """DB 세션을 받아 사용하되, commit/rollback하지 않음"""
    item = db.query(Item).filter(...).first()
    return item
```

---

## 9. 상수 관리

### Manager 내부 상수
```python
class EnhanceManager:
    MAX_ITEM_LEVEL = 20
    ENHANCE_BASE_COST = 100
    ENHANCE_STAT_MULTIPLIER = 0.10
```

### 규칙
- Manager 클래스 최상단에 대문자로 선언
- 매직 넘버 금지 — 모든 수치에 이름을 부여
- 여러 Manager에서 공유하는 상수는 `config.py`로 이동
- 기획 수치(밸런스)는 CSV 메타데이터로 관리 (코드 상수 X)

---

## 10. 금지 패턴 (Anti-patterns)

```python
# ❌ 클라이언트 값을 그대로 신뢰
user.gold += data.get("gold_amount")  # 클라이언트가 금액을 결정

# ✅ 서버가 계산
reward_gold = cls._calculate_gold_reward(monster, player_level)
user.gold += reward_gold

# ❌ DB 세션을 여러 Manager 간 공유
db = SessionLocal()
InventoryManager.equip(db, ...)    # 다른 Manager에 세션 전달
BattleManager.reward(db, ...)

# ✅ 각 Manager가 자체 트랜잭션 관리
await InventoryManager.equip_item(user_no, data)
await BattleManager.battle_result(user_no, data)

# ❌ commit 후 같은 세션으로 추가 작업
db.commit()
db.query(User).filter(...)  # 위험: 커밋된 세션 재사용

# ❌ except 블록에서 비즈니스 에러 처리
try:
    item = db.query(Item).filter(...).first()
    if not item:
        raise ValueError("아이템 없음")  # 비즈니스 에러를 예외로 던짐
except ValueError:
    return error_response(...)

# ✅ 비즈니스 에러는 조건문으로 처리
item = db.query(Item).filter(...).first()
if not item:
    return error_response(ErrorCode.ITEM_NOT_FOUND, "아이템 없음")
```
