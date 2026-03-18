---
name: web-client
description: "웹 RPG 클라이언트 개발 가이드. Phaser.js 전투 애니메이션 + HTML/CSS UI. 서버 시뮬레이션 결과를 클라이언트에서 재생하는 뷰어 패턴. 모바일 확장 대비 설계."
---

# Web Client 개발 가이드

## 아키텍처 원칙

### 클라이언트 = 뷰어
- 전투 로직은 서버에서 시뮬레이션, 결과를 `battle_log[]`로 반환
- 클라이언트는 battle_log를 순서대로 재생 (애니메이션/연출)
- 클라이언트에 게임 로직 없음 → 치팅 원천 차단

### 기술 분담
| 영역 | 기술 | 용도 |
|------|------|------|
| 전투 화면 | Phaser.js | 스프라이트 애니메이션, 이펙트, 전투 연출 |
| UI | HTML/CSS | 인벤토리, 스탯, 메뉴, 스테이지 선택 등 |
| 통신 | fetch API | `POST /api` 단일 게이트웨이 |

### 디렉토리 구조
```
fastapi/public/
├── index.html              # SPA 엔트리
├── css/
│   ├── variables.css       # CSS 변수 (테마 컬러, 등급 컬러)
│   ├── common.css          # 공통 레이아웃
│   └── components/         # 컴포넌트별 CSS
├── js/
│   ├── app.js              # 앱 초기화, 라우터
│   ├── api.js              # 서버 통신 (apiCall)
│   ├── session.js          # 세션 관리
│   ├── screens/            # 화면별 JS
│   │   ├── login.js
│   │   ├── town.js
│   │   ├── inventory.js
│   │   ├── stage-select.js
│   │   └── battle.js
│   └── phaser/             # Phaser.js 전투 씬
│       ├── BootScene.js
│       ├── BattleScene.js
│       └── ResultScene.js
└── assets/
    ├── backgrounds/        # 챕터/스테이지 배경
    ├── sprites/            # 캐릭터/몬스터 스프라이트
    └── effects/            # 이펙트 스프라이트
```

---

## 서버 통신

### 단일 게이트웨이
모든 요청은 `POST /api` 하나로 수렴 (REST가 아닌 RPC 스타일).

### 세션 인증
- 로그인 시 서버가 `session_id` 반환 → localStorage에 저장
- 이후 모든 요청에 `Authorization: Bearer {session_id}` 헤더 포함
- 세션 TTL: 7일
- 인증 불필요 API: 1002(게임 데이터 로드), 1003(유저 생성/로그인)

### apiCall 함수
```javascript
async function apiCall(apiCode, data = {}) {
    const headers = { 'Content-Type': 'application/json' };
    const sessionId = localStorage.getItem('session_id');
    if (sessionId) {
        headers['Authorization'] = `Bearer ${sessionId}`;
    }

    const res = await fetch('/api', {
        method: 'POST',
        headers,
        body: JSON.stringify({
            api_code: apiCode,
            data: data
        })
    });
    return res.json();
}
```

> **주의**: 요청 바디에 `user_no` 불필요. 서버가 세션에서 추출.

### 응답 형식

**성공**:
```json
{
    "success": true,
    "message": "설명",
    "data": { ... }
}
```

**실패**:
```json
{
    "success": false,
    "error_code": "E1002",
    "message": "에러 설명"
}
```

### 에러 코드 체계
| 범위 | 분류 | 주요 코드 |
|------|------|-----------|
| E1xxx | 시스템/인증 | E1001 알 수 없는 API, E1002 인증 실패(세션 만료), E1003 권한 없음 |
| E2xxx | 유저 | E2001 유저 없음, E2002 이미 존재 |
| E3xxx | 인벤토리 | E3001 아이템 없음, E3002 장착 불가, E3003 코스트 초과, E3004 인벤 가득 |
| E4xxx | 전투 | E4001 스테이지 없음, E4002 잘못된 요청, E4003 미해금 |
| E9xxx | 서버 내부 | E9001 DB 오류, E9002 Redis 오류, E9999 알 수 없음 |

### 에러 핸들링 패턴
```javascript
async function apiCall(apiCode, data = {}, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const res = await fetch('/api', { ... });
            const json = await res.json();

            if (!json.success) {
                if (json.error_code === 'E1002') {
                    // 세션 만료 → 로그인 화면으로
                    localStorage.removeItem('session_id');
                    router.navigate('login');
                    return null;
                }
                // 그 외 에러 → UI에 message 표시
                showError(json.message);
                return json;
            }
            return json;
        } catch (e) {
            // 네트워크 에러 → 지수 백오프 재시도
            if (i < retries - 1) {
                await sleep(1000 * Math.pow(2, i));
            }
        }
    }
    showError('서버 연결 실패');
    return null;
}
```

---

## API 명세 (전체)

### 1002 — 게임 데이터 로드 (인증 불필요)
앱 시작 시 1회 호출. 메타데이터를 클라이언트 메모리에 캐싱.
```
요청: { "api_code": 1002, "data": {} }
응답.data: {
    monsters: { [monster_idx]: { name, monster_base, size_type, base_hp, base_atk, ... } },
    drop_config: { ... },
    equip_bases: [ { item_base, main_group, sub_group, req_level, ... } ],
    prefixes: [ { prefix_korean, equipment_type, stat_1, ... } ],
    uniques: [ { item_name, item_type, ... } ],
    ...
}
```

### 1003 — 유저 생성/로그인 (인증 불필요)
닉네임 기반. 신규면 생성, 기존이면 로그인.
```
요청: { "api_code": 1003, "data": { "user_name": "닉네임" } }
응답.data: { user_no, user_name, session_id }
```
> `session_id`를 localStorage에 저장할 것.

### 2001 — 장비 장착
```
요청: { "api_code": 2001, "data": { "item_uid": "uuid", "equip_slot": "weapon" } }
응답.data: { item_uid, equip_slot }
```
> equip_slot: "weapon" | "armor" | "helmet" | "gloves" | "boots"
> 같은 슬롯에 이미 장비가 있으면 자동 해제 후 장착.

### 2002 — 장비 해제
```
요청: { "api_code": 2002, "data": { "item_uid": "uuid" } }
응답.data: { item_uid }
```

### 2003 — 인벤토리 조회
```
요청: { "api_code": 2003, "data": {} }
응답.data: {
    items: [
        {
            item_uid, base_item_id, item_level, rarity,
            item_cost, suffix_id, set_id,
            dynamic_options: { base_atk, base_aspd, atk_pct, ... },
            equip_slot       // 장착 중이면 슬롯명, 미장착이면 null
        },
        ...
    ]
}
```

### 3001 — 전투 시뮬레이션
```
요청: { "api_code": 3001, "data": { "monster_idx": 1, "spawn_type": "일반" } }
응답.data: {
    result: "win" | "lose" | "timeout",
    battle_log: [ ... ],        // 아래 battle_log 구조 참조
    rewards: {                   // 승리 시에만
        exp_gained, gold_gained,
        level, exp, leveled_up, gold
    }
}
```

### 3002 — 몬스터 킬 & 드롭 처리
```
요청: { "api_code": 3002, "data": {
    "monster_idx": 2101, "spawned_level": 30,
    "spawned_grade": 2, "field_level": 3, "spawn_type": "정예"
} }
응답.data: { drops: [ ... ] }
```

### 3003 — 스테이지 입장
```
요청: { "api_code": 3003, "data": { "stage_id": 1 } }
응답.data: {
    stage_id: 1,
    monsters: [
        { wave: 1, monsters: [ { monster_idx, spawn_type }, ... ] },
        { wave: 2, monsters: [ ... ] },
        { wave: 3, monsters: [ ..., { monster_idx, spawn_type: "보스" } ] }
    ]
}
```
> 웨이브 1,2: 일반4 + 정예1 / 웨이브 3: 일반4 + 정예1 + 보스1

### 3004 — 스테이지 클리어
```
요청: { "api_code": 3004, "data": { "stage_id": 1 } }
응답.data: { stage_id, unlocked_next, current_stage }
```
> enter_stage 이후에만 호출 가능. 아니면 E4002.

### 3005 — 방치 파밍 ON/OFF
```
ON 요청:  { "api_code": 3005, "data": { "stage_id": 5 } }
OFF 요청: { "api_code": 3005, "data": {} }
응답.data: { idle_active: true|false, stage_id? }
```

### 3006 — 방치 파밍 보상 수령
```
요청: { "api_code": 3006, "data": {} }
응답.data: { elapsed_minutes, kill_count, gold_reward, total_gold }
```

---

## 게임 플레이 흐름

### 전체 흐름
```
[로그인] → 1003 유저 생성/로그인
    ↓
[초기 로드] → 1002 게임 데이터 + 2003 인벤토리
    ↓
[마을] → 장비 관리 / 스테이지 선택 / 방치 파밍 관리
    ↓
[스테이지 진행]
    3003 스테이지 입장 → 웨이브/몬스터 목록 수신
        ↓
    웨이브 1~3 순차 진행:
        몬스터마다 → 3001 전투 + 3002 드롭 처리
        ↓
    전체 클리어 시 → 3004 스테이지 클리어 (다음 해금)
    ↓
[마을 귀환] → 드롭 확인, 장비 교체, 다음 도전
```

### 스토리 모드 vs 재입장(던전 모드)
- **스토리 모드** (최초 진행): 포탈 귀환 가능, 진행 위치 서버 저장
- **재입장** (클리어 후 파밍): 포탈 귀환 불가, 자동 반복 ON/OFF 가능

---

## Phaser.js 전투 연출

### 씬 구조
```
BootScene       → 에셋 프리로드 (배경, 스프라이트, 이펙트)
BattleScene     → 전투 연출 (battle_log 재생)
ResultScene     → 전투 결과/보상 표시
```

### battle_log 구조
서버가 반환하는 각 턴의 데이터:
```json
{
    "turn": 1,              // 행동 순서 (1부터 순차)
    "actor": "player",      // "player" 또는 "monster"
    "action": "attack",     // "attack" 또는 "miss"
    "damage": 35,           // 데미지 (miss면 0)
    "crit": false,          // 치명타 여부
    "target_hp": 250        // 대상의 남은 HP
}
```

### battle_log 재생 패턴
```javascript
playBattleLog(log, speedMultiplier = 1) {
    let index = 0;
    const baseDelay = 600;
    this.time.addEvent({
        delay: baseDelay / speedMultiplier,
        repeat: log.length - 1,
        callback: () => {
            const entry = log[index++];
            this.executeAction(entry);
        }
    });
}

executeAction(entry) {
    const { actor, action, damage, crit, target_hp } = entry;

    if (action === 'miss') {
        this.showMissText(actor === 'player' ? 'monster' : 'player');
        return;
    }

    // 공격 모션
    this.playAttackAnim(actor);

    // 데미지 텍스트 (치명타면 강조)
    const target = actor === 'player' ? 'monster' : 'player';
    this.showDamageText(target, damage, crit);

    // HP 바 갱신
    this.updateHpBar(target, target_hp);
}
```

### 연출 요소
| 요소 | 설명 |
|------|------|
| 공격 모션 | 스프라이트 이동 + 공격 프레임 |
| 데미지 텍스트 | 팝업 숫자 (crit=true → 크게, 빨간색) |
| MISS 텍스트 | 회색 "MISS" 팝업 |
| HP 바 | 실시간 tween으로 감소 |
| 전투 속도 | 1x / 2x / 스킵 (speedMultiplier) |

### 에셋 관리
- 스프라이트시트: 캐릭터/몬스터 애니메이션 프레임
- 배경: 챕터/스테이지별 PNG (이미 `resources/`에 7종 존재)
- 레이지 로딩: 현재 챕터 에셋만 로드, 다음 챕터는 백그라운드 프리로드
- 오브젝트 풀링: 데미지 텍스트, 이펙트 파티클 재사용

---

## HTML/CSS UI

### 레이아웃 규칙
- 모바일 퍼스트 (portrait 기준 설계)
- 터치 타겟: 최소 44px × 44px
- `pointerdown` 이벤트 사용 (`click` 대신)
- 반응형: CSS Grid/Flexbox, 고정 px 금지

### 화면 구성
| 화면 | 주요 요소 |
|------|-----------|
| 로그인 | 닉네임 입력, 에러 메시지 |
| 마을 (허브) | 스테이지 선택, 인벤토리, 스탯, 시설 버튼, 방치 파밍 상태 |
| 인벤토리 | 아이템 그리드, 장착 슬롯 5개, 코스트 게이지, 세트 현황 |
| 스테이지 선택 | 7챕터 × 3스테이지, 해금 상태, 챕터 보스 |
| 전투 | Phaser.js 캔버스 (배경 + 캐릭터 + 몬스터 + 이펙트) |
| 전투 결과 | 승/패, 경험치 바, 골드, 드롭 아이템 목록 |
| 방치 파밍 | 타이머, 현재 스테이지, 보상 수령 버튼 |

### CSS 변수
```css
:root {
    /* 죄종 테마 컬러 */
    --color-wrath: #dc2626;
    --color-envy: #16a34a;
    --color-greed: #ca8a04;
    --color-sloth: #6b7280;
    --color-gluttony: #ea580c;
    --color-lust: #db2777;
    --color-pride: #7c3aed;

    /* 아이템 등급 컬러 */
    --color-normal: #9ca3af;
    --color-magic: #3b82f6;
    --color-rare: #eab308;
    --color-craft: #22c55e;
    --color-unique: #a855f7;
}
```

### 아이템 등급 표시
| 등급 | 테두리 색 | 배경 | 비고 |
|------|-----------|------|------|
| normal | 회색 | - | 초기 장비 |
| magic | 파랑 | - | 접두 OR 접미 1개 |
| rare | 노랑 | - | 접두 + 접미 2개 |
| craft | 초록 | - | 제작, 죄종 선택 |
| unique | 보라 | 미광 효과 | 보스 전용 |

### 코스트 게이지
```
최대 코스트 = (레벨 × 1) + (코스트스탯 × 2)
현재 코스트 = Σ 장착 장비의 item_cost
```
> 남은 코스트를 시각적으로 표시. 초과 시 장착 불가(E3003).

---

## 모바일 확장 대비

### PWA 준비
- `manifest.json`: 앱 이름, 아이콘, `display: standalone`
- Service Worker: 오프라인 에셋 캐싱
- HTTPS 필수

### 앱 래핑 (향후)
- Capacitor로 네이티브 앱 빌드
- 웹 코드 변경 최소화

---

## 성능 체크리스트

- [ ] 초기 로딩 3초 이내
- [ ] 전투 씬 60 FPS 유지
- [ ] 에셋 총 용량 챕터당 5MB 이하
- [ ] 탭 비활성화 시 애니메이션 일시정지 (`visibilitychange`)
- [ ] 메모리 릭 방지: 씬 전환 시 리스너/타이머 정리
