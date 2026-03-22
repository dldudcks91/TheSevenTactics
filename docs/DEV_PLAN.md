# TheSevenTactics 개발 계획서

> TheSevenRPG의 서버/클라이언트 구조를 기반으로 TheSevenTactics에 맞게 재구성

---

## 기술 스택 (TheSevenRPG에서 계승)

| 구분 | 기술 |
|------|------|
| 서버 | FastAPI (async) + uvicorn |
| DB | MySQL + SQLAlchemy ORM |
| 캐시 | Redis (async, 세션/전투 상태) |
| 클라이언트 | Vanilla JS (ES Modules) + Phaser.js |
| 데이터 | CSV 메타데이터 (서버 시작 시 로드) |
| API | 단일 /api 게이트웨이 (api_code 라우팅) |
| 인증 | Redis 세션 (Bearer 토큰) |
| 폰트 | Galmuri11 (픽셀, 한/영) |
| PWA | Service Worker |

---

## TheSevenRPG → TheSevenTactics 전환 분석

### 그대로 가져올 수 있는 것

| 모듈 | 파일/구조 | 비고 |
|------|----------|------|
| 서버 프레임워크 | main.py, config.py, database.py, logger.py | 프로젝트명만 변경 |
| API 게이트웨이 | APIManager.py, schemas.py | api_code 라우팅 구조 동일 |
| 인증/세션 | SessionManager.py, UserInitManager.py | 로그인/가입/세션 동일 |
| Redis 관리 | RedisManager.py, redis_types.py, base 클래스들 | 그대로 복사 |
| DB 관리 | DBManager.py, user_init_db_manager.py | 그대로 복사 |
| 에러 코드 | ErrorCode.py | 확장하여 사용 |
| 클라 SPA 구조 | app.js, store.js, api.js, session.js, utils.js | 그대로 복사 |
| 클라 CSS | variables.css, common.css, 컴포넌트 CSS | 복사 후 수정 |
| 로그인 화면 | screens/login.js | 그대로 복사 |
| .claude/ 규칙/스킬 | server.md, client.md, workflow.md, 스킬들 | 복사 후 수정 |

### 구조 복사 → 내용 교체

| 모듈 | 원본 | 변경 내용 |
|------|------|----------|
| CSV 메타데이터 | monster_info, stage_info, chapter_info 등 | 영웅/스킬트리/선술집 데이터 추가 |
| 스테이지/챕터 | StageManager.py | 7챕터 × 4스테이지 구조 유지, 내용 교체 |
| 아이템 시스템 | InventoryManager.py, ItemDropManager.py | 장비 구조 유지, 죄악 접사 교체 |
| 스탯 시스템 | UserStat 모델 | str/dex/vit/luck/cost → str/int/agi/vit/will |
| 클라 메인 화면 | main.js, tabs/, views/ | 영웅/파티/선술집 탭 추가 |

### 새로 작성

| 모듈 | 설명 | 우선순위 |
|------|------|---------|
| **Hero 모델** | 영웅 보유 테이블 (고유패시브, 스킬트리, 등급, 진영) | Phase 2 |
| **HeroSkillTree 모델** | 영웅별 스킬트리 포인트 배분 | Phase 2 |
| **Party 모델** | 3인 파티 편성 | Phase 2 |
| **Tavern 모델** | 선술집 방문 영웅 상태 | Phase 2 |
| **HeroManager** | 영웅 영입/관리/스킬트리 투자 | Phase 3 |
| **TavernManager** | 선술집 영웅 방문/영입 로직 | Phase 3 |
| **PartyManager** | 파티 편성/변경 | Phase 3 |
| **BattleManager (3v3)** | 3v3 파티 자동전투 시뮬레이션 | Phase 3 |
| **7죄종 스킬트리 CSV** | 7개 트리 × 스킬 목록 | Phase 3 |
| **영웅 목록 CSV** | 영웅 기본 정보 + 고유 패시브 | Phase 3 |
| **영웅 관리 UI** | 영웅 목록/상세/스킬트리 화면 | Phase 4 |
| **파티 편성 UI** | 3인 파티 드래그/배치 | Phase 4 |
| **선술집 UI** | 방문 영웅 확인/영입 화면 | Phase 4 |
| **3v3 전투 UI** | Phaser.js 3v3 전투 애니메이션 | Phase 4 |

---

## 개발 Phase

### Phase 1: 프로젝트 뼈대 복사

**목표**: TheSevenRPG의 서버/클라 구조를 그대로 가져와 실행 가능한 상태로 만듦

```
작업 목록:
□ fastapi/ 디렉토리 구조 복사
  - main.py, config.py, database.py, logger.py, schemas.py
  - services/system/ (APIManager, GameDataManager, SessionManager, UserInitManager, ErrorCode)
  - services/db_manager/ (DBManager, user_init_db_manager)
  - services/redis_manager/ (전체)
  - requirements.txt
□ public/ 디렉토리 복사
  - index.html, manifest.json, sw.js
  - css/ (전체)
  - js/ (app.js, api.js, store.js, session.js, utils.js, meta-data.js)
  - js/screens/login.js
□ .claude/ 규칙/스킬 복사 및 수정
□ .env 설정 (DB명: TheSevenTactics)
□ 서버 실행 확인 (로그인/가입 동작)
```

### Phase 2: DB 모델 재설계 ✅

**목표**: TheSevenTactics 핵심 데이터 모델 정의

```
기존 모델 (수정):
✅ User — gold, current_stage 유지
✅ UserStat — 5스탯 재정의 (STR/DEX/VIT/LCK/INT)
✅ Item — 장비 시스템 3부위 (weapon/armor/accessory)

신규 모델:
✅ Hero — 영웅 보유 정보
  - hero_uid (PK), user_no (FK), hero_id, grade (등급)
  - skill_tree_1, skill_tree_2 (7죄종 중 2개)
  - tree1_points JSON, tree2_points JSON (스킬 포인트 배분)
  - level, exp, job, faction, passive_id, active_id
✅ Party — 파티 편성
  - user_no (PK), slot_1 (hero_uid), slot_2 (hero_uid), slot_3 (hero_uid)
✅ Tavern — 선술집 상태
  - user_no (PK), hero_id, grade, faction, skill_tree_1, skill_tree_2
  - passive_id, active_id, arrived_at (방문 시각), expires_at (만료 시각)

삭제 모델:
✅ Collection, Card — 카드/컬렉션 시스템 제거
✅ BattleSession — 3v3용으로 재설계
```

### Phase 3: 핵심 시스템 구현 ✅

**목표**: 게임의 고유 시스템 구현

```
CSV 메타데이터:
✅ hero_base.csv — 영웅 28명 (바알 포함, 이름/진영/스탯/패시브/액티브)
✅ skill_tree.csv — 7죄종 × 4스킬 = 28스킬 (트리ID, 레벨별 효과, 코스트)
✅ tavern_config.csv — 등급 확률, 영입 비용, 체류 시간

서버 매니저:
✅ HeroManager — 영웅 조회(4001)/상세(4002)/스킬트리 투자(4003)
✅ TavernManager — 선술집 조회(5001)/영입(5002)/거절(5003)
✅ PartyManager — 파티 조회(6001)/편성(6002)
✅ BattleManager (3v3) — 3인 파티 vs 몬스터 자동전투 시뮬레이션(3001)
  - 행동력 기반 턴제 + 바알 지휘관 시스템
  - 기본 공격 + 액티브 스킬 + 스킬트리 패시브
  - 진영 시너지 + 죄악 시너지 적용
  - 상태이상 7종 (StatusEffectManager)
  - 드롭 연동 (ItemDropManager)

API 코드:
✅ 4xxx: 영웅 관련 (4001 조회, 4002 상세, 4003 스킬투자)
✅ 5xxx: 선술집 관련 (5001 조회, 5002 영입, 5003 거절)
✅ 6xxx: 파티 관련 (6001 조회, 6002 편성)
```

### Phase 4: 클라이언트 UI ✅

**목표**: 게임 화면 구현

```
탭:
✅ 영웅 탭 — 보유 영웅 목록, 상세 정보, 스킬트리 투자 UI
✅ 파티 탭 — 3인 파티 편성, 시너지 미리보기
✅ 장비 탭 — 장비 장착/해제 (영웅별) + EquipmentManager (API 2001~2003)
✅ 스킬트리 탭 — 7죄종 트리 시각화, 레벨핍 표시, 포인트 배분

뷰:
✅ 마을 뷰 — 선술집 버튼 추가
✅ 선술집 뷰 — 방문 영웅 표시, 영입/거절 UI
✅ 스테이지 선택 뷰 — 기존 구조 유지
✅ 전투 뷰 — Phaser.js 3v3 전투 애니메이션
  - 아군/적 유닛 사각 스프라이트 + 이름/HP바
  - 공격 모션, 피격 흔들림, 데미지 숫자 팝업
  - x1/x2/x4 배속 컨트롤
  - 전투 로그 + 결과 오버레이
```

---

## 핵심 설계 결정사항 (확정)

| 항목 | 결정 |
|------|------|
| 직업 시스템 | 5직업 (warrior/knight/mage/assassin/healer) — 영웅 특성으로 결정, 전직 없음 |
| 역할 태그 | 공격/방어/지원/방해 (UI 가이드용, 시스템 제약 아님) |
| 장비 슬롯 | 전원 3부위 (무기/갑옷/장신구) |
| 파티 | 영웅 3인 자유 편성 (바알은 HoMM3식 지휘관 — 슬롯 차지 안 함) |
| 영웅 보유 | 같은 영웅 1체만 |
| 영웅 구조 | 고유 패시브+액티브(고정) + 베이스 스탯(고정) + 진영(고정) + 등급(랜덤) + 스킬트리 2개(랜덤) |
| 스킬트리 | 7죄종, 영웅당 2개 보유, 유저가 포인트 직접 배분 |
| 영웅 획득 | 선술집에 시간마다 랜덤 방문 → 골드로 영입 |
| 전투 | 3v3 자동전투, 행동력 기반 턴제 |
| 진영 | 인간 / 악마 / 천상 (3진영 시너지) |
| 용병 대여 | 없음 — 모든 영웅은 내 것 |

---

## 기획 완료 항목

- [x] 스탯 체계 확정: STR/DEX/VIT/LCK/INT (CST→INT 변경, 코스트 삭제)
- [x] 바알 = HoMM3식 지휘관 (전투 밖에서 레벨 기반 버프 제공, 슬롯 차지 안 함)
- [x] 직업 5종 확정: warrior/knight/mage/assassin/healer (전직 없음, 영웅 특성으로 결정)
- [x] 장비 3부위: 무기/갑옷/장신구
- [x] 카드 시스템 삭제 → 스킬트리 직접 투자 방식
- [x] 전투 공식 이식: ATK × (1-DEF/(DEF+100)) × 사이즈 × 치명타
- [x] 상태이상 7종 이식 (화상/중독/스턴/빙결/침식/매혹/심판)
- [x] 몬스터 시스템 이식: 16베이스 × 3타입, 정예 특성, 사이즈 보정
- [x] 드롭 시스템 이식: mlvl 기반, 등급별 확률, 타겟 파밍 3축
- [x] 장비 등급/접사/세트 이식: 매직/레어/크래프트/유니크, 7죄종 세트 보너스
- [x] 경험치/레벨 이식: Lv1~50, 지수 곡선, 사망 패널티 10%
- [x] CSV 19개 이식: equipment, monster, stage, drop, spawn, elite, status 등

## Phase 6: RPG 시스템 이식 ✅

```
서버:
✅ models.py — 장비 3부위 전환 (weapon/armor/accessory)
✅ models.py — STR/DEX/VIT/LCK/INT 스탯 확정
✅ EquipmentManager — 3부위 장착/해제 + remap_slot() 매핑
✅ ItemDropManager — mlvl 기반 드롭 생성 + 3부위 매핑
✅ BattleManager — 드롭 연동 (전투 승리 시 아이템 지급)
✅ StatusEffectManager — 상태이상 7종 (burn/poison/stun/freeze/corrode/charm/judge)
✅ GameDataManager — CSV 23개 로드 + drop_equip_weights 3부위 매핑
✅ BattleManager — StatusEffectManager 통합 (stun 행동불가, judge 스킬차단, freeze 속도감소)

클라이언트:
✅ 장비 탭 — 3부위 UI (weapon/armor/accessory)
✅ 전투 결과 — 드롭 아이템 표시 (BattleManager 응답에 포함)
✅ 인벤토리 화면 — 아이템 목록/상세/장착/판매
```

## Phase 7-S: 전투 시스템 고도화 (서버, 예정)

**목표**: INT 스탯 효과 확정 + 포지션(전열/후열) + 직업별 AI 타겟팅

### 변경 파일

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `services/rpg/BattleManager.py` | 수정 | A: INT→matk 분리, B: 포지션 보정, C: AI 타겟팅 |
| `models.py` | 수정 | B: Party에 pos_1/pos_2/pos_3 컬럼 추가 |
| `services/rpg/PartyManager.py` | 수정 | B: 포지션 편성 API 반영 |

### A. INT 스탯 세부 효과

```
현재: final_atk = max(atk, matk) → 무조건 높은 쪽 사용
변경: 직업 기반 분리

1. _build_ally_unit 수정
   - warrior/knight/assassin → atk (STR 기반) 사용
   - mage/healer → matk (INT 기반) 사용

2. INT 스킬 증폭
   - skill_mult *= (1 + total_int * 0.003)
   - INT 100이면 스킬 데미지 +30%

3. INT → 마법 방어력 기여
   - mdef = total_int * 0.3
   - 마법 공격 피격 시 mdef로 경감
```

### B. 포지션 시스템 (전열/후열)

```
1. Party 모델 변경
   - pos_1 = Column(String(10), default="front")  # front/back
   - pos_2 = Column(String(10), default="front")
   - pos_3 = Column(String(10), default="front")

2. PartyManager.set_party API 확장
   - data: {"slot_1": uid, "pos_1": "front", "slot_2": uid, "pos_2": "back", ...}

3. 포지션 보정 (BattleManager)
   - 전열: 받는 피해 100%, 적 타겟 우선순위 높음
   - 후열: 받는 피해 -20%, 주는 피해 -10%, 타겟 우선순위 낮음
   - mage/healer는 후열 패널티(주는 피해 -10%) 면제 (원거리 직업)
```

### C. 전투 AI/타겟팅 개선

```
현재: target = min(targets, key=lambda t: t["hp"]) → 무조건 최저 HP

변경: 직업별 타겟 선택

- warrior:  전열 우선 → HP 낮은 적
- knight:   전열 우선 → HP 낮은 적 (+ 아군 보호 패시브)
- mage:     마법방어 낮은 적 우선
- assassin: 후열 우선 → HP 낮은 적 (백어택)
- healer:   적 공격은 최저 HP (향후: 아군 힐 스킬)
```

---

## 미구현 항목 (향후)

- [ ] 스킬트리 상세 설계 (7트리 × N스킬, 수치 밸런싱)
- [ ] 영웅 베이스 스탯 밸런싱 (hero_base.csv)
- [ ] 장비 접사 수치 밸런싱 (ilvl/qlvl 체계)
- [ ] 드롭 확률 테이블 세부 조정
- [ ] 대장간 (크래프팅) 구현
- [ ] 장비 강화/분해 시스템
- [ ] PvP 투기장
- [ ] 오프라인 훈련 (연옥)
- [ ] 길드/세력 시스템
- [ ] 퀘스트 게시판

---

## Phase 7: 클라이언트 UI 보강 (기획 확정 → 미구현)

> 기획서(GAME_DESIGN.md)에 확정되었으나 클라이언트에 아직 반영되지 않은 항목

### A. 기획 확정 → 클라이언트 미구현

```
- [ ] A1. 포지션 (전열/후열) 배치 UI
      - 파티 편성 시 유저가 전열/후열 지정
      - 전열(슬롯1,2) 우선 피격, 후열(슬롯3) 보호
      - 전열 전멸 시 후열 → 전열 전환
      - 범위 스킬은 열 무시
      - 관련 파일: party.js, prebattle-view.js, BattleManager.py

- [ ] A2. 전투 설정 (전투 전 전략)
      - 스킬 우선순위 설정
      - 타겟 우선순위 (HP 낮은 적 / 뒤열 / 앞열)
      - 포션 사용 조건 (HP N% 이하 시 자동 사용)
      - 관련 파일: prebattle-view.js, BattleManager.py

- [ ] A3. 객잔 시설 구현
      - 게임 시작 시 해금 (거점 시설)
      - HP 회복 기능
      - 포션 구매 시스템
      - 관련 파일: town-view.js, 신규 inn-view.js

- [ ] A4. 세트 보너스 UI
      - 7죄종 세트 2/4/6 브레이크포인트 표시
      - 현재 장착 세트 포인트 카운트
      - 세트 효과 활성/비활성 시각적 구분
      - 관련 파일: equip.js, hero.js

- [ ] A5. 장비 비교 뷰
      - 장비 장착 시 현재 vs 새 장비 스탯 비교
      - 상승/하락 수치 색상 표시 (녹색/빨간색)
      - 관련 파일: equip.js
```

### B. 기획서 내부 불일치 (정리 필요)

```
- [ ] B1. 장비 부위 수 통일
      - GAME_DESIGN.md: 5부위 (무기/갑옷/투구/장갑/신발)
      - DEV_PLAN.md 확정: 3부위 (무기/갑옷/장신구)
      → GAME_DESIGN.md §7 수정 필요

- [ ] B2. 전직 시스템 기술 통일
      - GAME_DESIGN.md §6: "전직: 일정 레벨 도달 시 5직업 중 택1"
      - DEV_PLAN.md 확정: "전직 없음 (영웅 특성으로 결정)"
      → GAME_DESIGN.md §3, §6 수정 필요

- [ ] B3. 스킬트리/특성 구조 통일
      - GAME_DESIGN.md §9: "전직 시 죄종 택1 → 특성풀 개방"
      - DEV_PLAN.md 확정: "영웅당 2개 트리 보유, 포인트 직접 배분"
      → GAME_DESIGN.md §9 수정 필요
```

### C. UX 개선 (선택)

```
- [ ] C1. 파티 편성 시 진영 시너지 미리보기
- [ ] C2. 영웅 상세 → 장비 현황 연결
- [ ] C3. 스킬트리 시각화 (리스트형 → 트리/그래프형)
```

---

*마지막 업데이트: 2026-03-22*
