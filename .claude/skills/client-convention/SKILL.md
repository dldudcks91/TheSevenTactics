---
name: client-convention
description: "클라이언트 코딩 컨벤션. ES Modules, Screen 라이프사이클, Store 상태관리, DOM 렌더링 패턴, 이벤트 위임, CSS 규칙, Phaser.js 연동 규칙. 클라이언트 코드 작성 시 반드시 따라야 할 코드 레벨 규칙."
---

# Client Convention — 클라이언트 코딩 컨벤션

클라이언트(fastapi/public/) 코드 작성 시 반드시 따르는 코드 레벨 규칙.
아키텍처와 API 명세는 `web-client` 스킬 참조.

---

## §1. 모듈 시스템

### ES Modules 사용 (빌드 도구 없음)

모든 JS 파일은 ES Modules로 작성한다. IIFE 패턴을 사용하지 않는다.

```javascript
// ✅ 올바른 패턴
export function doSomething() { ... }
export class SomeComponent { ... }

// ✅ 기본 내보내기 (Screen, Store 등 파일당 1개 모듈)
export default InventoryScreen;

// ❌ 금지: IIFE
const Module = (() => { ... })();
```

### import 규칙

```javascript
// 1. 코어 모듈 (app, store, api)
import { Store } from '../store.js';
import { apiCall } from '../api.js';

// 2. 컴포넌트
import { ItemCard } from '../components/item-card.js';

// 3. 상수/유틸
import { EQUIP_SLOTS, formatGold } from '../utils.js';
```

- 경로는 항상 **상대 경로** + **`.js` 확장자 포함** (브라우저 ES Modules 필수)
- 외부 라이브러리(Phaser 등)는 CDN `<script>` 태그로 로드, import하지 않음

### index.html 엔트리

```html
<!-- 외부 라이브러리: CDN -->
<script src="https://cdn.jsdelivr.net/npm/phaser@3.80.1/dist/phaser.min.js" defer></script>

<!-- 앱 엔트리: 단 1개의 module 스크립트 -->
<script type="module" src="js/app.js"></script>
```

- `<script>` 태그는 **app.js 하나만** 등록
- 나머지 모듈은 app.js에서 import 체인으로 로드됨
- 기존 IIFE 파일들의 `<script>` 나열 제거

---

## §2. 디렉토리 구조

```
fastapi/public/
├── index.html                  # 엔트리 (script type="module" 1개)
├── css/
│   ├── variables.css           # CSS 변수 (테마, 등급, 공통)
│   ├── common.css              # 레이아웃, 타이포, 공통 요소
│   └── screens/                # 화면별 CSS (Screen 이름과 1:1)
│       ├── login.css
│       ├── town.css
│       ├── inventory.css
│       └── battle.css
├── js/
│   ├── app.js                  # 앱 초기화 + 라우터 + Screen 등록
│   ├── api.js                  # apiCall (서버 통신)
│   ├── store.js                # 중앙 상태 관리 (pub/sub)
│   ├── session.js              # 세션 (localStorage)
│   ├── constants.js            # 클라이언트 상수
│   ├── utils.js                # 포맷터, DOM 헬퍼
│   ├── screens/                # 화면 모듈 (Screen 인터페이스)
│   │   ├── login.js
│   │   ├── town.js
│   │   ├── inventory.js
│   │   ├── stage-select.js
│   │   ├── battle.js
│   │   ├── idle-farm.js
│   │   └── cards.js
│   ├── components/             # 재사용 UI 컴포넌트
│   │   ├── item-card.js
│   │   ├── stat-panel.js
│   │   ├── hp-bar.js
│   │   └── tooltip.js
│   └── phaser/                 # Phaser.js 전투 씬
│       ├── BattleScene.js
│       └── ResultScene.js
└── assets/
    ├── backgrounds/
    ├── sprites/
    └── effects/
```

### 네이밍 규칙

| 대상 | 규칙 | 예시 |
|------|------|------|
| 파일명 | kebab-case | `stage-select.js`, `item-card.js` |
| Screen 모듈 | PascalCase 객체 | `StageSelectScreen` |
| Component 함수/클래스 | PascalCase | `ItemCard`, `HpBar` |
| 일반 함수/변수 | camelCase | `apiCall`, `formatGold` |
| 상수 | UPPER_SNAKE_CASE | `MAX_INVENTORY`, `EQUIP_SLOTS` |
| CSS 클래스 | kebab-case | `.item-card`, `.stat-chip` |
| data 속성 | kebab-case | `data-action="sell"`, `data-item-uid="..."` |

---

## §3. Screen 모듈

### Screen 인터페이스

모든 화면 모듈은 아래 인터페이스를 구현한다:

```javascript
// js/screens/inventory.js
import { Store } from '../store.js';
import { apiCall } from '../api.js';

const InventoryScreen = {
    /** @type {HTMLElement} */
    el: null,

    /** @type {Object} DOM 참조 캐시 */
    refs: {},

    /** @type {Function[]} Store 구독 해제 함수 목록 */
    _unsubscribers: [],

    // ── [1] 마운트: 구조 생성 + 참조 캐싱 + 이벤트 바인딩 + Store 구독 ──
    mount(el) {
        this.el = el;

        // 최초 1회만 DOM 생성
        if (!el.dataset.initialized) {
            el.innerHTML = `...`;
            el.dataset.initialized = 'true';
        }

        // DOM 참조 캐싱
        this.refs = {
            goldEl: el.querySelector('#inv-gold'),
            itemGrid: el.querySelector('.item-grid'),
        };

        // 이벤트 위임 (컨테이너에 1개)
        this._handleEvent = this.handleEvent.bind(this);
        el.addEventListener('pointerdown', this._handleEvent);

        // Store 구독
        this._unsubscribers.push(
            Store.subscribe('user.gold', (gold) => this.renderGold(gold))
        );

        // 초기 데이터 로드
        this.loadData();
    },

    // ── [2] 언마운트: 구독 해제 + 타이머 정리 ──
    unmount() {
        if (this._handleEvent) {
            this.el.removeEventListener('pointerdown', this._handleEvent);
        }
        this._unsubscribers.forEach(unsub => unsub());
        this._unsubscribers = [];
    },

    // ── [3] 데이터 로드 ──
    async loadData() { ... },

    // ── [4] 렌더링 (부분 갱신) ──
    renderGold(gold) { ... },

    // ── [5] 이벤트 핸들러 ──
    handleEvent(e) { ... },
};

export default InventoryScreen;
```

### Screen 라이프사이클 규칙

| 규칙 | 설명 |
|------|------|
| `mount()`에서 innerHTML은 **최초 1회만** | `el.dataset.initialized` 체크로 중복 생성 방지 |
| DOM 참조는 `this.refs`에 캐싱 | `querySelector`를 렌더링마다 반복 호출하지 않음 |
| Store 구독은 `mount()`에서, 해제는 `unmount()`에서 | 메모리 릭 방지 |
| 타이머(`setInterval`)도 `unmount()`에서 정리 | 화면 전환 후에도 타이머가 돌면 안 됨 |
| `loadData()`는 `mount()` 마지막에 호출 | DOM 준비 완료 후 API 호출 |

---

## §4. Store (상태 관리)

### 구조

```javascript
// js/store.js
const Store = {
    _state: {},
    _listeners: {},  // key → Set<callback>

    /** 값 읽기 (dot notation) */
    get(key) {
        return key.split('.').reduce((obj, k) => obj?.[k], this._state);
    },

    /** 값 쓰기 + 구독자 알림 */
    set(key, value) {
        const keys = key.split('.');
        let target = this._state;
        for (let i = 0; i < keys.length - 1; i++) {
            if (!target[keys[i]]) target[keys[i]] = {};
            target = target[keys[i]];
        }
        target[keys[keys.length - 1]] = value;

        // 해당 key 구독자 알림
        this._notify(key, value);
    },

    /** 구독 — 해제 함수 반환 */
    subscribe(key, callback) {
        if (!this._listeners[key]) this._listeners[key] = new Set();
        this._listeners[key].add(callback);

        // 해제 함수 반환
        return () => this._listeners[key].delete(callback);
    },

    /** 구독자 알림 */
    _notify(key, value) {
        const listeners = this._listeners[key];
        if (listeners) {
            listeners.forEach(cb => cb(value));
        }
    },

    /** 여러 값 일괄 업데이트 (알림은 각각) */
    merge(obj, prefix = '') {
        for (const [k, v] of Object.entries(obj)) {
            const fullKey = prefix ? `${prefix}.${k}` : k;
            if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
                this.merge(v, fullKey);
            } else {
                this.set(fullKey, v);
            }
        }
    },
};

export { Store };
```

### Store 키 구조

```javascript
// 유저 기본 정보
Store.set('user.gold', 15000);
Store.set('user.level', 25);
Store.set('user.exp', 3200);
Store.set('user.stat_points', 5);

// 스탯
Store.set('stats.str', 30);
Store.set('stats.dex', 20);
Store.set('stats.vit', 15);
Store.set('stats.luck', 10);
Store.set('stats.cost', 5);

// 인벤토리 (배열은 통째로)
Store.set('inventory.items', [...]);

// 방치 파밍
Store.set('idle.active', true);
Store.set('idle.stage_id', 5);
```

### Store 사용 규칙

| 규칙 | 설명 |
|------|------|
| **API 응답 → Store 반영** | API 성공 후 관련 Store 키 업데이트 |
| **Store → UI 렌더링** | Store 구독 콜백에서 DOM 갱신 |
| **UI → API → Store → UI** | 직접 DOM을 수정하지 않고, Store를 거침 |
| **Store에 넣지 않는 것** | 전투 로그(일회성), 메타데이터(불변), 폼 입력값(로컬) |
| **subscribe 반환값 보관** | `_unsubscribers` 배열에 push → unmount에서 일괄 해제 |

### 데이터 흐름 원칙

```
[유저 액션] → apiCall() → [서버 응답]
                              ↓
                        Store.set(key, value)
                              ↓
                        구독 콜백 실행
                              ↓
                        DOM 부분 갱신
```

Screen이 직접 API 응답으로 DOM을 수정하지 않는다.
**반드시 Store를 경유**하여 모든 화면이 동기화되도록 한다.

```javascript
// ✅ 올바른 패턴
async function sellItem(itemUid) {
    const result = await apiCall(2004, { item_uid: itemUid });
    if (result.success) {
        Store.set('user.gold', result.data.total_gold);   // Store 경유
        // → Store 구독자(마을 골드, 인벤토리 골드)가 자동 갱신
    }
}

// ❌ 금지: API 응답으로 직접 DOM 수정
async function sellItem(itemUid) {
    const result = await apiCall(2004, { item_uid: itemUid });
    document.querySelector('#gold').textContent = result.data.total_gold;
}
```

---

## §5. API 통신

### apiCall 사용 패턴

```javascript
// js/api.js
import { Store } from './store.js';
import { showToast } from './utils.js';

const MAX_RETRIES = 3;
const BASE_DELAY = 1000;

/**
 * 서버 API 호출
 * @param {number} apiCode
 * @param {object} data
 * @returns {Promise<object|null>} 응답 또는 null (세션 만료 시)
 */
export async function apiCall(apiCode, data = {}) {
    const sessionId = localStorage.getItem('session_id');
    const headers = { 'Content-Type': 'application/json' };
    if (sessionId) {
        headers['Authorization'] = `Bearer ${sessionId}`;
    }

    const body = JSON.stringify({ api_code: apiCode, data });

    for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
        try {
            const res = await fetch('/api', { method: 'POST', headers, body });
            const result = await res.json();

            if (!result.success) {
                handleApiError(result);
            }
            return result;

        } catch (err) {
            if (attempt < MAX_RETRIES - 1) {
                await new Promise(r => setTimeout(r, BASE_DELAY * 2 ** attempt));
            }
        }
    }

    showToast('서버에 연결할 수 없습니다.', 'error');
    return null;
}
```

### Screen에서의 API 호출 패턴

```javascript
// Screen 내부
async loadData() {
    Loading.show();
    try {
        const result = await apiCall(2003);
        if (result?.success) {
            Store.set('inventory.items', result.data.items);
        }
    } finally {
        Loading.hide();
    }
},

async handleSell(itemUid) {
    const result = await apiCall(2004, { item_uid: itemUid });
    if (result?.success) {
        Store.set('user.gold', result.data.total_gold);

        // 인벤토리 목록에서 제거
        const items = Store.get('inventory.items')
            .filter(i => i.item_uid !== itemUid);
        Store.set('inventory.items', items);
    }
},
```

### API 통신 규칙

| 규칙 | 설명 |
|------|------|
| Loading 표시 | 초기 데이터 로드 시 `Loading.show()` / `Loading.hide()` |
| null 체크 | `result?.success`로 null (네트워크 실패) 처리 |
| Store 반영 | 성공 시 반드시 관련 Store 키 업데이트 |
| 에러 토스트 | `api.js`의 `handleApiError`에서 일괄 처리, Screen에서 중복 표시 안 함 |
| 세션 만료 | `api.js`에서 감지 → 로그인 화면 이동 (Screen 관여 불필요) |

---

## §6. DOM 렌더링

### 3단계 렌더링 패턴

```
[1단계] innerHTML — 구조 생성 (mount 시 최초 1회)
[2단계] refs 캐싱 — querySelector로 동적 요소 참조 저장
[3단계] 부분 갱신 — refs를 통해 textContent/style 등 변경
```

### 1단계: 구조 생성

```javascript
mount(el) {
    if (!el.dataset.initialized) {
        el.innerHTML = `
            <div class="inventory-screen">
                <div class="inv-header">
                    <span id="inv-gold">0 G</span>
                </div>
                <div class="item-grid" id="item-grid"></div>
            </div>
        `;
        el.dataset.initialized = 'true';
    }
}
```

### 2단계: refs 캐싱

```javascript
this.refs = {
    goldEl: el.querySelector('#inv-gold'),
    itemGrid: el.querySelector('#item-grid'),
};
```

### 3단계: 부분 갱신

```javascript
// ✅ 텍스트/속성 변경 — refs 사용
renderGold(gold) {
    this.refs.goldEl.textContent = `${gold.toLocaleString()} G`;
},

// ✅ 리스트 렌더링 — innerHTML (컨테이너 단위)
renderItems(items) {
    this.refs.itemGrid.innerHTML = items.map(item => `
        <div class="item-card rarity-${item.rarity}"
             data-action="select-item"
             data-item-uid="${item.item_uid}">
            <span class="item-name">${this.escapeHtml(item.name)}</span>
            <span class="item-level">+${item.item_level}</span>
        </div>
    `).join('');
},
```

### XSS 방지

서버/유저 데이터를 innerHTML에 넣을 때 반드시 이스케이프한다:

```javascript
// js/utils.js
export function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
```

```javascript
// ✅ 유저 입력 포함 시
el.innerHTML = `<span>${escapeHtml(userName)}</span>`;

// ✅ 또는 생성 후 textContent로 설정
el.querySelector('.name').textContent = userName;

// ❌ 금지: 유저 데이터 직접 삽입
el.innerHTML = `<span>${userName}</span>`;  // XSS 취약
```

### 렌더링 규칙

| 규칙 | 설명 |
|------|------|
| innerHTML은 **컨테이너 단위**로 사용 | 전체 Screen을 re-render하지 않음 |
| 유저/서버 데이터 → `escapeHtml()` 또는 `textContent` | XSS 방지 |
| 단일 값 변경 → `refs.el.textContent = value` | innerHTML 재생성 불필요 |
| 리스트 변경 → `refs.grid.innerHTML = items.map(...)` | 리스트 컨테이너만 교체 |
| `data-*` 속성으로 데이터 전달 | 이벤트 위임에서 사용 |

---

## §7. 이벤트 처리

### 이벤트 위임 패턴

Screen/컴포넌트당 **컨테이너에 이벤트 리스너 1개**만 등록한다.

```javascript
mount(el) {
    // 리스너 1개로 모든 하위 요소 이벤트 처리
    this._handleEvent = this.handleEvent.bind(this);
    el.addEventListener('pointerdown', this._handleEvent);
},

handleEvent(e) {
    const target = e.target.closest('[data-action]');
    if (!target) return;

    const action = target.dataset.action;
    const itemUid = target.dataset.itemUid;

    switch (action) {
        case 'sell':      this.handleSell(itemUid); break;
        case 'equip':     this.handleEquip(itemUid); break;
        case 'enhance':   this.handleEnhance(itemUid); break;
    }
},

unmount() {
    this.el.removeEventListener('pointerdown', this._handleEvent);
},
```

### HTML에서 data-action 사용

```html
<button data-action="sell" data-item-uid="uuid-123">판매</button>
<button data-action="equip" data-item-uid="uuid-123" data-slot="weapon">장착</button>
```

### 이벤트 규칙

| 규칙 | 설명 |
|------|------|
| `pointerdown` 사용 | `click` 대신 (모바일 300ms 지연 방지) |
| 이벤트 위임 | 개별 요소에 리스너 금지, 컨테이너에 1개 |
| `closest('[data-action]')` | 클릭 대상에서 가장 가까운 action 요소 탐색 |
| `unmount()`에서 해제 | `removeEventListener` 필수 |
| 키보드 이벤트 | `keydown` 사용, Enter 키 처리 등 |

```javascript
// ❌ 금지: 개별 요소마다 리스너
items.forEach(item => {
    el.querySelector(`#item-${item.uid}`).addEventListener('pointerdown', () => { ... });
});

// ❌ 금지: onclick 인라인
el.innerHTML = `<button onclick="sell('${uid}')">판매</button>`;
```

---

## §8. CSS 규칙

### 파일 구성

- `variables.css` — CSS 변수 (색상, 간격, 폰트 등)
- `common.css` — 공통 레이아웃, 타이포, 유틸 클래스
- `screens/{screen-name}.css` — 화면별 CSS (Screen 이름과 1:1 대응)

### CSS 변수 체계

```css
:root {
    /* ── 죄종 테마 ── */
    --color-wrath: #dc2626;
    --color-envy: #16a34a;
    --color-greed: #ca8a04;
    --color-sloth: #6b7280;
    --color-gluttony: #ea580c;
    --color-lust: #db2777;
    --color-pride: #7c3aed;

    /* ── 아이템 등급 ── */
    --color-normal: #9ca3af;
    --color-magic: #3b82f6;
    --color-rare: #eab308;
    --color-craft: #22c55e;
    --color-unique: #a855f7;

    /* ── UI 공통 ── */
    --color-bg: #1a1a2e;
    --color-surface: #16213e;
    --color-text: #e0e0e0;
    --color-text-dim: #888;
    --color-success: #22c55e;
    --color-warning: #f59e0b;
    --color-error: #ef4444;

    /* ── 간격 ── */
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;

    /* ── 터치 타겟 최소 크기 ── */
    --touch-min: 44px;
}
```

### 스코핑 규칙

화면별 CSS는 Screen 루트 클래스로 스코핑한다:

```css
/* screens/inventory.css */
.inventory-screen { ... }
.inventory-screen .item-grid { ... }
.inventory-screen .item-card { ... }
```

### CSS 규칙

| 규칙 | 설명 |
|------|------|
| 모바일 퍼스트 | portrait 기준 설계, 데스크톱은 media query로 확장 |
| 터치 타겟 | 버튼/인터랙티브 요소 최소 `44px × 44px` |
| 고정 px 금지 | 레이아웃에 `%`, `rem`, `fr` 사용. 간격/보더만 px 허용 |
| CSS 변수 사용 | 색상, 간격 등 매직 값 직접 사용 금지 |
| 등급별 스타일 | `.rarity-normal`, `.rarity-magic` 등 클래스로 색상 적용 |
| Flexbox/Grid 사용 | float, position:absolute 남용 금지 |

---

## §9. Phaser.js 연동

### 경계 원칙

```
HTML/CSS 영역 (Screen)          Phaser 영역 (Canvas)
├── 인벤토리                      ├── 전투 배경
├── 스탯 화면                     ├── 캐릭터/몬스터 스프라이트
├── 스테이지 선택                  ├── 공격 모션/이펙트
├── 마을 허브                     ├── 데미지 텍스트
└── 전투 결과 UI                  └── HP 바 (인게임)
```

| 규칙 | 설명 |
|------|------|
| Phaser는 **전투 연출(BattleScene)에만** 사용 | UI, 메뉴, 인벤토리에 Phaser 사용 금지 |
| 전투 결과 UI는 **HTML/CSS** | 승리/패배 팝업, 보상 목록 등 |
| Phaser → Screen 통신 | Phaser 씬에서 커스텀 이벤트 발행, Screen에서 수신 |
| Screen → Phaser 통신 | Screen에서 Phaser game 인스턴스의 씬 메서드 호출 |

### BattleScreen 구조

```javascript
// js/screens/battle.js
const BattleScreen = {
    game: null,

    mount(el) {
        if (!el.dataset.initialized) {
            el.innerHTML = `
                <div class="battle-screen">
                    <div id="phaser-container"></div>
                    <div class="battle-ui">
                        <button data-action="speed-1x">1x</button>
                        <button data-action="speed-2x">2x</button>
                        <button data-action="skip">스킵</button>
                    </div>
                </div>
            `;
            el.dataset.initialized = 'true';
        }

        // Phaser 인스턴스 생성
        this.game = new Phaser.Game({
            parent: 'phaser-container',
            scene: [BattleScene],
            // ...config
        });

        this._handleEvent = this.handleEvent.bind(this);
        el.addEventListener('pointerdown', this._handleEvent);
    },

    unmount() {
        // Phaser 인스턴스 파괴 (메모리 릭 방지)
        if (this.game) {
            this.game.destroy(true);
            this.game = null;
        }
        this.el.removeEventListener('pointerdown', this._handleEvent);
    },
};
```

### Phaser 씬 규칙

| 규칙 | 설명 |
|------|------|
| `unmount()` 시 `game.destroy(true)` | Canvas, 타이머, 리스너 정리 |
| 에셋은 현재 챕터만 로드 | 메모리 절약, 다음 챕터는 백그라운드 프리로드 |
| 오브젝트 풀링 | 데미지 텍스트, 이펙트 파티클 재사용 |
| `visibilitychange` 감지 | 탭 비활성 시 애니메이션 일시정지 |

---

## §10. 금지 패턴

### 모듈/구조

```javascript
// ❌ IIFE 모듈
const Module = (() => { ... })();

// ❌ 전역 변수
window.gameData = { ... };

// ❌ import 없이 전역 참조
Store.set(...);  // import { Store } 없이 사용

// ❌ 순환 의존
// a.js: import from './b.js'
// b.js: import from './a.js'
```

### 상태 관리

```javascript
// ❌ API 응답으로 직접 DOM 수정 (Store 우회)
const result = await apiCall(2004, data);
document.querySelector('#gold').textContent = result.data.gold;

// ❌ Store 구독 해제 안 함 (메모리 릭)
mount(el) {
    Store.subscribe('user.gold', this.renderGold);
    // unmount에서 해제 안 함
}

// ❌ 게임 로직을 클라이언트에서 계산
const damage = playerAtk * (1 - monsterDef / 100);  // 서버가 할 일
```

### DOM/이벤트

```javascript
// ❌ 개별 요소마다 리스너
items.forEach(item => {
    el.querySelector(`#${item.uid}`).addEventListener('click', handler);
});

// ❌ click 이벤트 (모바일 지연)
el.addEventListener('click', handler);

// ❌ innerHTML에 유저 데이터 직접 삽입
el.innerHTML = `<span>${userName}</span>`;

// ❌ onclick 인라인 핸들러
el.innerHTML = `<button onclick="doSomething()">`;

// ❌ mount()마다 innerHTML 재생성
mount(el) {
    el.innerHTML = `...`;  // initialized 체크 없음 → 매번 재생성
}
```

### 성능

```javascript
// ❌ 렌더링 루프에서 querySelector
function render() {
    document.querySelector('#gold').textContent = gold;  // refs 사용해야 함
}

// ❌ setInterval 정리 안 함
mount(el) {
    setInterval(updateTimer, 1000);  // unmount에서 clearInterval 안 함
}

// ❌ Phaser game.destroy() 안 함
unmount() {
    // game 인스턴스 파괴 안 하고 화면만 전환 → 메모리 릭
}
```
