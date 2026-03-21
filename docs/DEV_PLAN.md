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

### Phase 2: DB 모델 재설계

**목표**: TheSevenTactics 핵심 데이터 모델 정의

```
기존 모델 (수정):
□ User — gold, current_stage 유지
□ UserStat — 5스탯 재정의 (str/int/agi/vit/will)
□ Item — 장비 시스템 3부위 (weapon/armor/accessory)

신규 모델:
□ Hero — 영웅 보유 정보
  - hero_uid (PK), user_no (FK), hero_id, grade (등급)
  - skill_tree_1, skill_tree_2 (7죄종 중 2개)
  - tree1_points JSON, tree2_points JSON (스킬 포인트 배분)
  - level, exp
□ Party — 파티 편성
  - user_no (PK), slot_1 (hero_uid), slot_2 (hero_uid), slot_3 (hero_uid)
□ Tavern — 선술집 상태
  - user_no (PK), hero_id, grade, skill_tree_1, skill_tree_2
  - arrived_at (방문 시각), expires_at (만료 시각)

삭제 모델:
□ Collection, Card — 카드/컬렉션 시스템 제거
□ BattleSession — 3v3용으로 재설계
```

### Phase 3: 핵심 시스템 구현

**목표**: 게임의 고유 시스템 구현

```
CSV 메타데이터:
□ hero_base.csv — 영웅 기본 정보 (이름, 진영, 스탯 프로필, 고유 패시브, 액티브 스킬)
□ skill_tree.csv — 7죄종 스킬트리 (트리ID, 스킬 목록, 레벨별 효과)
□ tavern_config.csv — 선술집 설정 (방문 주기, 등급 확률, 영입 비용)

서버 매니저:
□ HeroManager — 영웅 조회/스킬트리 투자/레벨업
□ TavernManager — 영웅 방문 생성/영입/거절
□ PartyManager — 파티 편성/변경/조회
□ BattleManager (3v3) — 3인 파티 vs 몬스터 자동전투 시뮬레이션
  - 행동력 기반 턴제
  - 기본 공격 + 액티브 스킬 + 스킬트리 패시브
  - 진영 시너지 + 죄악 시너지 적용

API 코드 추가:
□ 4xxx: 영웅 관련 (조회, 스킬트리 투자, 레벨업)
□ 5xxx: 선술집 관련 (방문 확인, 영입, 거절)
□ 6xxx: 파티 관련 (편성, 변경, 조회)
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

## 미구현 항목 (향후)

- [ ] INT 스탯 세부 효과 확정 (마법 공격력, 스킬 증폭)
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

*마지막 업데이트: 2026-03-21*
