/**
 * TheSevenTactics — Battle View
 * 3v3 자동전투 결과 표시
 */
import { apiCall } from '../../api.js';
import { Store } from '../../store.js';
import { formatGold } from '../../utils.js';

const BattleView = {
    el: null,
    _stageId: null,
    _result: null,

    mount(el, data) {
        this.el = el;
        this._stageId = data?.stageId;
        if (this._stageId) {
            this._startBattle();
        } else {
            el.innerHTML = '<div class="battle-view"><div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted)">스테이지를 선택해주세요</div></div>';
        }
    },
    unmount() {},

    async _startBattle() {
        this.el.innerHTML = '<div class="battle-view"><div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-primary)">전투 중...</div></div>';

        const result = await apiCall(3001, { stage_id: this._stageId });
        if (result?.success) {
            this._result = result.data;
            // 유저 데이터 업데이트
            if (result.data.user) {
                const u = result.data.user;
                Store.set('user.level', u.level);
                Store.set('user.exp', u.exp);
                Store.set('user.gold', u.gold);
                Store.set('user.stat_points', u.stat_points);
                Store.set('user.current_stage', u.current_stage);
            }
            this._render();
        } else {
            this.el.innerHTML = `<div class="battle-view"><div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--color-error)">${result?.message || '전투 오류'}</div></div>`;
        }
    },

    _render() {
        const d = this._result;
        const isVictory = d.result === 'victory';
        const log = d.battle_log || [];
        const rewards = d.rewards || {};

        let html = `<div class="battle-view">
            <div class="battle-header">
                <span class="battle-title">전투 결과</span>
                <button class="btn battle-back" data-action="back-town">마을로</button>
            </div>
            <div class="battle-result">
                <div class="battle-result-text ${d.result}">${isVictory ? '승리!' : '패배...'}</div>
                ${isVictory ? `<div class="battle-rewards">EXP +${rewards.exp} · ${formatGold(rewards.gold)}</div>` : ''}
            </div>
            <div class="battle-log">`;

        for (const entry of log) {
            const critClass = entry.crit ? ' crit' : '';
            html += `<div class="battle-log-entry${critClass}">
                [${entry.turn}] ${entry.actor} → ${entry.target} ${entry.damage}dmg${entry.crit ? ' CRIT!' : ''} (HP:${entry.target_hp})
            </div>`;
        }

        html += '</div></div>';
        this.el.innerHTML = html;

        this.el.onclick = (e) => {
            if (e.target.closest('[data-action="back-town"]')) {
                // main.js의 switchRightView를 호출하기 위해 이벤트 발행
                import('../views/town-view.js').then(() => {
                    // MainScreen에 접근하기 위한 우회
                    import('../../main.js').then(m => m.default.switchRightView('town'));
                });
            }
        };
    },
};

export default BattleView;
