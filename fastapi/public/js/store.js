/**
 * TheSevenRPG — Central Store (pub/sub)
 * 중앙 상태 관리: API 응답 → Store → UI 갱신
 */
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

        this._notify(key, value);
    },

    /** 구독 — 해제 함수 반환 */
    subscribe(key, callback) {
        if (!this._listeners[key]) this._listeners[key] = new Set();
        this._listeners[key].add(callback);

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
