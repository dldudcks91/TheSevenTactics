/**
 * TheSevenTactics — Battle View (아포칼립스 스타일)
 *
 * 레이아웃: 초상화 + 이름/레벨 + HP바 + 행동게이지
 * 아군 좌측(초상화 왼쪽, 바 오른쪽), 적 우측(초상화 오른쪽, 바 왼쪽)
 */
import { apiCall } from '../../api.js';
import { Store } from '../../store.js';
import { formatGold } from '../../utils.js';

/* ── 색상 ─────────────────────────── */
const C_HP_BG     = 0x1a0a10;
const C_HP_ALLY   = 0x30c050;   // 초록
const C_HP_ENEMY  = 0xc03030;   // 빨강
const C_GAUGE_BG  = 0x0a1018;
const C_GAUGE     = 0xf0c030;   // 노랑 (행동 게이지)
const C_SKILL_GAUGE = 0x6080f8; // 파랑 (스킬 게이지)
const C_PORTRAIT_BG = 0x101020;
const C_FRAME_ALLY = 0x4080c0;
const C_FRAME_ENEMY = 0x903030;
const C_FRAME_BOSS = 0xd0a020;

const FC_TINT = { demon: 0xd0a0ff, human: 0xa0c8ff, celestial: 0xfff0a0 };
const GC_FRAME = { common: 0x606060, uncommon: 0x4080c0, rare: 0xd0a020, legendary: 0xc060f8 };

const STATUS_ICON = { burn: '🔥', freeze: '❄️', poison: '☠️', charm: '💜' };
const STATUS_COLOR = { burn: '#f06030', freeze: '#60c0f8', poison: '#60d060', charm: '#d060d0' };

/* ── 크기 상수 ────────────────────── */
const PORTRAIT = 96;     // 초상화 크기
const BAR_W = 110;       // HP/게이지 바 폭
const BAR_H = 14;        // HP바 높이
const GAUGE_BAR_H = 7;   // 게이지 바 높이
const TICK = 500;
const GAUGE_TICK = 30;

const CH_BG = {
    1: '/assets/backgrounds/battle/ch1.png',
    2: '/assets/backgrounds/battle/ch2.png',
    3: '/assets/backgrounds/battle/ch3.png',
};

const BattleView = {
    el: null, _stageId: null, _result: null,
    _game: null, _scene: null, _speed: 1,
    _playing: false, _finished: false, _skipReq: false,

    mount(el, data) {
        this.el = el;
        this._stageId = data?.stageId;
        this._speed = 1; this._playing = false;
        this._finished = false; this._skipReq = false;
        this._result = null;
        if (el.parentElement) el.parentElement.style.overflowY = 'hidden';
        this._stageId ? this._startBattle() : this._msg('스테이지를 선택해주세요');
    },
    unmount() {
        if (this.el?.parentElement) this.el.parentElement.style.overflowY = '';
        this._destroyGame(); this.el = null;
    },
    _destroyGame() { if (this._game) { this._game.destroy(true); this._game = null; this._scene = null; } },

    async _startBattle() {
        this._msg('전투 준비 중<span class="bv-dots"></span>');
        const res = await apiCall(3001, { stage_id: this._stageId });
        if (!res?.success) { this._msg(res?.message || '전투 오류', true); this._addBackBtn(); return; }
        this._result = res.data;
        if (res.data.user) {
            const u = res.data.user;
            Store.set('user.level', u.level); Store.set('user.exp', u.exp);
            Store.set('user.gold', u.gold); Store.set('user.stat_points', u.stat_points);
            Store.set('user.current_stage', u.current_stage);
        }
        this._buildUI();
    },

    _buildUI() {
        const d = this._result;
        const st = d.stage || {};
        const syn = d.synergy;
        this.el.innerHTML = `<div class="battle-view">
            <div class="bv-header">
                <span class="bv-title">${st.stage_name || '전투'}</span>
                <div class="bv-header-right">
                    <button class="bv-speed-btn active" data-action="speed" data-v="1">x1</button>
                    <button class="bv-speed-btn" data-action="speed" data-v="2">x2</button>
                    <button class="bv-speed-btn" data-action="speed" data-v="4">x4</button>
                    <button class="btn bv-skip-btn" data-action="skip">SKIP</button>
                </div>
            </div>
            ${syn ? `<div class="bv-synergy"><span class="bv-syn-label">${syn.label}</span> ${syn.desc}</div>` : ''}
            <div class="bv-arena" id="bv-arena"></div>
            <div class="bv-log" id="bv-log"></div>
            <div class="bv-result-overlay bv-hidden" id="bv-result"></div>
        </div>`;
        this.el.onclick = (e) => {
            const a = e.target.closest('[data-action]')?.dataset?.action;
            if (!a) return;
            if (a === 'back') { this._destroyGame(); import('../../main.js').then(m => m.default.switchRightView('town')); }
            else if (a === 'speed') {
                this._speed = parseInt(e.target.closest('[data-action]').dataset.v) || 1;
                this.el.querySelectorAll('.bv-speed-btn').forEach(b => b.classList.remove('active'));
                e.target.closest('[data-action]').classList.add('active');
            }
            else if (a === 'skip') { this._skipReq = true; }
            else if (a === 'retry') { this._startBattle(); }
        };
        this._initPhaser();
    },

    _initPhaser() {
        const wrap = this.el?.querySelector('#bv-arena');
        if (!wrap || typeof Phaser === 'undefined') { this._fallback(); return; }
        const w = wrap.clientWidth || 600, h = wrap.clientHeight || 400;
        const self = this;
        const chapter = this._result?.stage?.chapter || 1;
        const bgUrl = CH_BG[chapter] || CH_BG[1];
        this._game = new Phaser.Game({
            type: Phaser.CANVAS, parent: wrap, width: w, height: h,
            backgroundColor: '#0a0a14',
            scene: {
                preload() {
                    this.load.image('bg', bgUrl);
                    this.load.image('spr_ally', '/assets/sprites/ally.png');
                    this.load.image('spr_enemy', '/assets/sprites/enemy.png');
                },
                create() { self._scene = this; self._sceneCreate(this, w, h); },
            },
            scale: { mode: Phaser.Scale.NONE },
            render: { pixelArt: true, antialias: false },
            audio: { noAudio: true },
        });
    },

    /* ════════════════════════════════════
       씬 생성 — 아포칼립스 레이아웃
       아군: 좌측 (초상화 | 바)
       적:   우측 (바 | 초상화)
    ════════════════════════════════════ */
    _sceneCreate(sc, W, H) {
        const d = this._result;
        const allies = d.allies || [], enemies = d.enemies || [];

        // 배경
        if (sc.textures.exists('bg')) {
            const bg = sc.add.image(W / 2, H / 2, 'bg').setDisplaySize(W, H).setAlpha(0.5);
        }
        sc.add.rectangle(W / 2, H / 2, W, H, 0x000000, 0.2);

        // 유닛 배치
        const units = {};
        const count = Math.max(allies.length, enemies.length, 1);
        const slotH = Math.min(PORTRAIT + 50, (H - 10) / count);  // 간격 넓힘
        const startY = (H - slotH * count) / 2 + slotH / 2;

        // 아군·적 양쪽을 중앙 쪽으로 밀착 배치
        const cardFullW = PORTRAIT + 6 + BAR_W;  // 초상화+바 전체 폭
        const centerGap = 150;                     // 아군-적 사이 간격
        const allyLeft = W / 2 - centerGap / 2 - cardFullW;
        const enemyRight = W / 2 + centerGap / 2 + cardFullW;

        allies.forEach((u, i) => {
            const cy = startY + i * slotH;
            const px = allyLeft + PORTRAIT / 2;
            const bx = allyLeft + PORTRAIT + 6;
            units[u.name] = this._mkUnit(sc, u, px, cy, bx, true);
        });

        enemies.forEach((u, i) => {
            const cy = startY + i * slotH;
            const px = enemyRight - PORTRAIT / 2;
            const bx = enemyRight - PORTRAIT - 6 - BAR_W;
            units[u.name] = this._mkUnit(sc, u, px, cy, bx, false);
        });

        // VS 인트로
        const vs = this._txt(sc, W / 2, H / 2, '⚔ VS ⚔', '#e03030', 28);
        vs.setAlpha(0);
        sc.tweens.add({
            targets: vs, alpha: 1, duration: 300, yoyo: true, hold: 500,
            onComplete: () => { vs.destroy(); this._playLog(sc, units, d.battle_log || []); },
        });
    },

    /* ════════════════════════════════════
       유닛 카드 생성 (아포칼립스 스타일)
    ════════════════════════════════════ */
    _mkUnit(sc, data, portraitX, cy, barX, isAlly) {
        const isBoss = data.is_boss;
        const pSize = isBoss ? PORTRAIT * 1.15 : PORTRAIT;

        // ── 초상화 프레임 ──
        const frameBg = sc.add.rectangle(portraitX, cy, pSize + 6, pSize + 6, 0x000000, 0.7);
        const frameColor = isAlly ? (GC_FRAME[data.grade] || C_FRAME_ALLY) : (isBoss ? C_FRAME_BOSS : C_FRAME_ENEMY);
        frameBg.setStrokeStyle(3, frameColor, 1);

        const portrait = sc.add.rectangle(portraitX, cy, pSize, pSize, C_PORTRAIT_BG);

        // 스프라이트
        let sprite = null;
        const sprKey = isAlly ? 'spr_ally' : 'spr_enemy';
        if (sc.textures.exists(sprKey)) {
            sprite = sc.add.image(portraitX, cy, sprKey);
            const fit = Math.min((pSize - 4) / sprite.width, (pSize - 4) / sprite.height);
            sprite.setScale(fit);
            if (!isAlly) sprite.setFlipX(true);
            if (isAlly) sprite.setTint(FC_TINT[data.faction] || 0xffffff);
            else sprite.setTint(isBoss ? 0xff6060 : 0xffa0a0);
        }

        // ── 이름 + 레벨 (초상화 위) ──
        const nameColor = isAlly ? '#a0c8ff' : (isBoss ? '#f8d830' : '#f0a0a0');
        const nameStr = (isBoss ? '★' : '') + data.name;
        const nameText = this._txt(sc, portraitX, cy - pSize / 2 - 12, nameStr, nameColor, 10);

        // ── HP바 (초상화 옆) ──
        const hpBarY = cy - 8;
        const hpGfx = sc.add.graphics();
        this._drawBar(hpGfx, barX, hpBarY, BAR_W, BAR_H, 1, isAlly ? C_HP_ALLY : C_HP_ENEMY);

        // HP 텍스트 (바 위)
        const hpLabel = this._txt(sc, barX + BAR_W / 2, hpBarY - 1,
            `${data.max_hp}/${data.max_hp}`, '#fff', 8);

        // ── 행동 게이지 바 (HP바 아래) ──
        const gaugeBarY = hpBarY + BAR_H + 3;
        const gaugeGfx = sc.add.graphics();
        this._drawBar(gaugeGfx, barX, gaugeBarY, BAR_W, GAUGE_BAR_H, 0, C_GAUGE);

        // ── 스킬 게이지 바 (행동 게이지 아래) ──
        const skillBarY = gaugeBarY + GAUGE_BAR_H + 3;
        const skillGfx = sc.add.graphics();
        this._drawBar(skillGfx, barX, skillBarY, BAR_W, GAUGE_BAR_H, 0, C_SKILL_GAUGE);
        // 스킬 라벨
        const skillLabel = data.active_name
            ? this._txt(sc, barX + BAR_W / 2, skillBarY - 1, data.active_name, '#8090c0', 7)
            : null;

        // ── 상태이상 아이콘 (스킬 게이지 아래) ──
        const statusX = barX + BAR_W / 2;
        const statusText = this._txt(sc, statusX, skillBarY + GAUGE_BAR_H + 8, '', '#fff', 10);

        // 이동할 파츠 그룹
        const body = frameBg;  // 대표 오브젝트 (위치 참조용)

        return {
            body, frameBg, portrait, sprite, nameText, hpGfx, hpLabel, gaugeGfx, skillGfx, skillLabel, statusText,
            x: portraitX, y: cy, barX,
            hpBarY, gaugeBarY, skillBarY,
            maxHp: data.max_hp, hp: data.max_hp,
            speed: data.speed || 10, gauge: 0,
            skillGauge: 0, skillGaugeMax: data.skill_gauge_max || 12,
            isAlly, isBoss, faction: data.faction,
        };
    },

    /* ── 바 그리기 (범용) ──────────── */
    _drawBar(gfx, x, y, w, h, ratio, fillColor) {
        gfx.clear();
        gfx.fillStyle(C_HP_BG, 1).fillRect(x, y, w, h);
        if (ratio > 0) {
            gfx.fillStyle(fillColor, 1);
            gfx.fillRect(x, y, Math.ceil(w * Math.min(1, ratio)), h);
        }
        gfx.lineStyle(1, 0x303050, 1).strokeRect(x, y, w, h);
    },

    _updateHp(unit, newHp) {
        unit.hp = Math.max(0, newHp);
        const ratio = unit.hp / unit.maxHp;
        this._drawBar(unit.hpGfx, unit.barX, unit.hpBarY, BAR_W, BAR_H,
            ratio, unit.isAlly ? C_HP_ALLY : C_HP_ENEMY);
        if (unit.hpLabel) unit.hpLabel.setText(`${unit.hp}/${unit.maxHp}`);
    },

    _updateGauge(unit, ratio) {
        this._drawBar(unit.gaugeGfx, unit.barX, unit.gaugeBarY, BAR_W, GAUGE_BAR_H,
            ratio, C_GAUGE);
    },
    _updateSkillGauge(unit, ratio) {
        this._drawBar(unit.skillGfx, unit.barX, unit.skillBarY, BAR_W, GAUGE_BAR_H,
            ratio, C_SKILL_GAUGE);
    },

    /* ── 이동 파츠 ─────────────────── */
    _moveParts(u) {
        return [u.frameBg, u.portrait, u.sprite, u.nameText, u.hpGfx, u.hpLabel, u.gaugeGfx, u.skillGfx, u.skillLabel, u.statusText].filter(Boolean);
    },

    /* ════════════════════════════════════
       게이지 기반 턴 재생
    ════════════════════════════════════ */
    _playLog(sc, units, log) {
        this._playing = true;
        const logEl = this.el?.querySelector('#bv-log');
        let idx = 0;
        const allUnits = Object.values(units);
        allUnits.forEach(u => { u.gauge = 0; });

        const fillGauges = () => {
            if (!this.el || !this._playing) return;
            if (this._skipReq) {
                while (idx < log.length) this._applyInstant(units, log[idx++], logEl);
                this._onEnd(); return;
            }
            if (idx >= log.length) { this._onEnd(); return; }

            const nextEntry = log[idx];
            const actorUnit = units[nextEntry.actor || nextEntry.target];

            const gaugeStep = () => {
                if (!this.el || !this._playing) return;
                if (this._skipReq) {
                    while (idx < log.length) this._applyInstant(units, log[idx++], logEl);
                    this._onEnd(); return;
                }

                let ready = false;
                const inc = 5 * this._speed;

                allUnits.forEach(u => {
                    if (u.hp <= 0) return;
                    u.gauge = Math.min(100, u.gauge + u.speed * inc * 0.08);
                    this._updateGauge(u, u.gauge / 100);
                    // 스킬 게이지도 동시 충전
                    u.skillGauge = Math.min(u.skillGaugeMax, u.skillGauge + u.speed * inc * 0.08);
                    this._updateSkillGauge(u, u.skillGauge / u.skillGaugeMax);
                    if (actorUnit && u === actorUnit && u.gauge >= 100) ready = true;
                });
                if (!actorUnit) ready = true;

                if (ready) {
                    if (actorUnit) {
                        actorUnit.gauge = 0;
                        this._updateGauge(actorUnit, 0);
                    }
                    playAction();
                } else {
                    sc.time.delayedCall(GAUGE_TICK / this._speed, gaugeStep);
                }
            };
            gaugeStep();
        };

        const playAction = () => {
            if (idx >= log.length) { this._onEnd(); return; }
            const e = log[idx++];
            this._logText(logEl, e);
            const after = () => sc.time.delayedCall(200 / this._speed, fillGauges);

            switch (e.type) {
                case 'attack': case 'skill':
                    if (e.type === 'skill') {
                        const su = units[e.actor];
                        if (su) { su.skillGauge = 0; this._updateSkillGauge(su, 0); }
                    }
                    this._animAttack(sc, units, e, e.type === 'skill', after); break;
                case 'counter':
                    this._animCounter(sc, units, e, after); break;
                case 'lifesteal':
                    this._animHeal(sc, units, e); after(); break;
                case 'status_apply':
                    this._animStatusApply(sc, units, e); after(); break;
                case 'status_tick':
                    this._animStatusTick(sc, units, e); after(); break;
                case 'phase':
                    this._animPhase(sc, e, after); break;
                default: after();
            }
        };
        sc.time.delayedCall(300, fillGauges);
    },

    /* ── 공격 ──────────────────────── */
    _animAttack(sc, units, e, isSkill, cb) {
        const atk = units[e.actor], tgt = units[e.target];
        if (!atk || !tgt) { cb(); return; }
        const spd = this._speed;
        const dx = tgt.x > atk.x ? 20 : -20;

        if (isSkill && e.skill_name) {
            const W = sc.sys.game.config.width, H = sc.sys.game.config.height;
            const sk = this._txt(sc, W / 2, H / 2 - 30, `【${e.skill_name}】`, '#f8d830', 16);
            sc.tweens.add({ targets: sk, alpha: 0, y: sk.y - 20, duration: 700 / spd, delay: 200 / spd, onComplete: () => sk.destroy() });
        }

        // 초상화 돌진
        sc.tweens.add({ targets: this._moveParts(atk), x: '+=' + dx, duration: 80 / spd, yoyo: true, ease: 'Quad.easeOut' });

        sc.time.delayedCall(100 / spd, () => {
            // 피격 플래시
            if (tgt.portrait) { tgt.portrait.fillColor = 0xffffff; sc.time.delayedCall(50 / spd, () => { tgt.portrait.fillColor = C_PORTRAIT_BG; }); }
            if (tgt.sprite) { tgt.sprite.setTint(0xffffff); sc.time.delayedCall(50 / spd, () => {
                if (tgt.isAlly) tgt.sprite.setTint(FC_TINT[tgt.faction] || 0xffffff);
                else tgt.sprite.setTint(tgt.isBoss ? 0xff6060 : 0xffa0a0);
            }); }

            // 흔들림
            sc.tweens.add({ targets: this._moveParts(tgt), x: '+=' + 5, duration: 30 / spd, yoyo: true, repeat: 2 });

            // 데미지 숫자 (화면 중앙 쪽에 크게)
            const W = sc.sys.game.config.width;
            const dmgX = tgt.isAlly ? W * 0.3 : W * 0.7;
            const col = e.crit ? '#f8c830' : '#ffffff';
            const sz = e.crit ? (isSkill ? 28 : 22) : (isSkill ? 20 : 16);
            const dt = this._txt(sc, dmgX + (Math.random() - 0.5) * 20, tgt.y - 10,
                `${e.crit ? '!' : ''}${e.damage}`, col, sz);
            sc.tweens.add({ targets: dt, y: dt.y - 30, alpha: 0, duration: 600 / spd, onComplete: () => dt.destroy() });

            this._updateHp(tgt, e.target_hp);
            if (e.target_hp <= 0) this._animDeath(sc, tgt);
            cb();
        });
    },

    /* ── 반격 ──────────────────────── */
    _animCounter(sc, units, e, cb) {
        const atk = units[e.actor], tgt = units[e.target];
        if (!atk || !tgt) { cb(); return; }
        const spd = this._speed;

        const ct = this._txt(sc, atk.x, atk.y - PORTRAIT / 2 - 22, '반격!', '#f8c830', 11);
        sc.tweens.add({ targets: ct, alpha: 0, duration: 400 / spd, delay: 200 / spd, onComplete: () => ct.destroy() });

        const dx = tgt.x > atk.x ? 14 : -14;
        sc.tweens.add({ targets: this._moveParts(atk), x: '+=' + dx, duration: 50 / spd, yoyo: true });

        sc.time.delayedCall(60 / spd, () => {
            const W = sc.sys.game.config.width;
            const dmgX = tgt.isAlly ? W * 0.3 : W * 0.7;
            const dt = this._txt(sc, dmgX, tgt.y - 10, String(e.damage), '#ff8040', 14);
            sc.tweens.add({ targets: dt, y: dt.y - 20, alpha: 0, duration: 400 / spd, onComplete: () => dt.destroy() });
            this._updateHp(tgt, e.target_hp);
            if (e.target_hp <= 0) this._animDeath(sc, tgt);
            cb();
        });
    },

    /* ── 흡혈 ──────────────────────── */
    _animHeal(sc, units, e) {
        const u = units[e.actor];
        if (!u) return;
        u.hp = Math.min(u.maxHp, e.actor_hp);
        this._updateHp(u, u.hp);
        const ht = this._txt(sc, u.x + 20, u.y - 10, `+${e.value}`, '#40d870', 12);
        sc.tweens.add({ targets: ht, y: ht.y - 16, alpha: 0, duration: 400 / this._speed, onComplete: () => ht.destroy() });
    },

    /* ── 상태이상 부여 ─────────────── */
    _animStatusApply(sc, units, e) {
        const tgt = units[e.target];
        if (!tgt) return;
        const icon = STATUS_ICON[e.status] || '⚡';
        const st = this._txt(sc, tgt.x, tgt.y - PORTRAIT / 2 - 24, icon, STATUS_COLOR[e.status] || '#fff', 16);
        sc.tweens.add({ targets: st, y: st.y - 12, alpha: 0, duration: 500 / this._speed, onComplete: () => st.destroy() });
        const cur = tgt.statusText.text || '';
        if (!cur.includes(icon)) tgt.statusText.setText(cur + icon);
    },

    /* ── 상태이상 틱 ───────────────── */
    _animStatusTick(sc, units, e) {
        const tgt = units[e.target];
        if (!tgt) return;
        if (e.value > 0) {
            const dt = this._txt(sc, tgt.x - 8, tgt.y, `-${e.value}`, STATUS_COLOR[e.status] || '#ff8040', 11);
            sc.tweens.add({ targets: dt, y: dt.y - 14, alpha: 0, duration: 400 / this._speed, onComplete: () => dt.destroy() });
            if (e.target_hp !== undefined) this._updateHp(tgt, e.target_hp);
            if (e.target_hp !== undefined && e.target_hp <= 0) this._animDeath(sc, tgt);
        }
        if (e.status === 'freeze' && tgt.portrait) {
            tgt.portrait.fillColor = 0x80c0f8;
            sc.time.delayedCall(300 / this._speed, () => { if (tgt.portrait) tgt.portrait.fillColor = C_PORTRAIT_BG; });
        }
    },

    /* ── 보스 페이즈 ───────────────── */
    _animPhase(sc, e, cb) {
        const W = sc.sys.game.config.width, H = sc.sys.game.config.height;
        sc.cameras.main.shake(300 / this._speed, 0.015);
        const col = e.phase === 3 ? '#ff4040' : '#f8c830';
        const pt = this._txt(sc, W / 2, H / 2, e.message || `Phase ${e.phase}`, col, 18);
        pt.setAlpha(0);
        sc.tweens.add({ targets: pt, alpha: 1, duration: 200 / this._speed, yoyo: true, hold: 600 / this._speed, onComplete: () => { pt.destroy(); cb(); } });
    },

    /* ── 사망 ──────────────────────── */
    _animDeath(sc, u) {
        const parts = this._moveParts(u);
        sc.tweens.add({ targets: parts, alpha: 0.15, duration: 300 / this._speed });
        const xm = this._txt(sc, u.x, u.y, '✕', '#f04040', 30);
        xm.setAlpha(0);
        sc.tweens.add({ targets: xm, alpha: 0.8, duration: 150 / this._speed });
    },

    /* ── SKIP 즉시 적용 ───────────── */
    _applyInstant(units, e, logEl) {
        this._logText(logEl, e);
        if (e.target_hp !== undefined) {
            const tgt = units[e.target];
            if (tgt) {
                this._updateHp(tgt, e.target_hp);
                if (e.target_hp <= 0) this._moveParts(tgt).forEach(o => { if (o) o.setAlpha(0.15); });
            }
        }
        if (e.type === 'lifesteal' && e.actor_hp !== undefined) {
            const u = units[e.actor]; if (u) this._updateHp(u, e.actor_hp);
        }
    },

    /* ── 결과 ──────────────────────── */
    _onEnd() {
        this._playing = false; this._finished = true;
        const d = this._result, v = d.result === 'victory';
        const el = this.el?.querySelector('#bv-result');
        if (!el) return;
        el.innerHTML = `<div class="bv-result-box" style="position:relative">
            <button class="close-x" data-action="back">✕</button>
            <div class="bv-result-text ${v ? 'victory' : 'defeat'}">${v ? '승 리 !' : '패 배...'}</div>
            ${v ? `<div class="bv-result-rewards"><span>EXP +${d.rewards.exp}</span><span>${formatGold(d.rewards.gold)}</span></div>` : ''}
            ${v && d.rewards.items?.length ? `<div class="bv-result-drops">${d.rewards.items.map(it => `<div class="bv-drop-item" style="color:${{magic:'#6688ff',rare:'#ffcc00',craft:'#ff6600',unique:'#ff44aa'}[it.rarity]||'#aaa'}">${it.item_name} (${it.rarity})</div>`).join('')}</div>` : ''}
            <div class="bv-result-btns">
                <button class="btn btn-primary" data-action="retry">${v ? '다시 전투' : '재도전'}</button>
                <button class="btn" data-action="back">마을로</button>
            </div>
        </div>`;
        el.classList.remove('bv-hidden');
    },

    /* ── 로그 텍스트 ───────────────── */
    _logText(logEl, e) {
        if (!logEl) return;
        const div = document.createElement('div');
        let cls = 'bv-log-entry', txt = '';
        switch (e.type) {
            case 'attack': cls += e.crit ? ' crit' : ''; txt = `${e.actor} → ${e.target} ${e.damage}dmg${e.crit ? ' CRIT!' : ''}`; break;
            case 'skill': cls += ' skill'; txt = `${e.actor} ★${e.skill_name}★ → ${e.target} ${e.damage}dmg${e.crit ? ' CRIT!' : ''}`; break;
            case 'counter': cls += ' counter'; txt = `${e.actor} 반격! → ${e.target} ${e.damage}dmg`; break;
            case 'lifesteal': cls += ' heal'; txt = `${e.actor} 흡혈 +${e.value}HP`; break;
            case 'status_apply': cls += ' status'; txt = `${e.target} ← ${STATUS_ICON[e.status] || ''} ${e.status} (${e.turns}턴)`; break;
            case 'status_tick': cls += ' status'; txt = `${e.target} ${STATUS_ICON[e.status] || ''} ${e.value > 0 ? `-${e.value}HP` : e.status}`; break;
            case 'phase': cls += ' phase'; txt = `⚠ ${e.message}`; break;
            default: txt = JSON.stringify(e);
        }
        div.className = cls; div.textContent = txt;
        logEl.appendChild(div); logEl.scrollTop = logEl.scrollHeight;
    },

    /* ── 유틸 ──────────────────────── */
    _txt(sc, x, y, text, color, size) {
        return sc.add.text(x, y, text, { fontFamily: 'Galmuri11 Bold, Galmuri11, monospace', fontSize: size + 'px', color }).setOrigin(0.5);
    },
    _msg(html, isErr) {
        if (!this.el) return;
        this.el.innerHTML = `<div class="battle-view"><div class="bv-center-msg${isErr ? ' bv-error' : ''}">${html}</div></div>`;
    },
    _addBackBtn() {
        if (!this.el) return;
        const b = document.createElement('button'); b.className = 'btn bv-back-btn'; b.textContent = '마을로'; b.setAttribute('data-action', 'back');
        this.el.querySelector('.battle-view')?.appendChild(b);
        this.el.onclick = (e) => { if (e.target.closest('[data-action="back"]')) { this._destroyGame(); import('../../main.js').then(m => m.default.switchRightView('town')); } };
    },
    _fallback() {
        const d = this._result, logEl = this.el?.querySelector('#bv-log');
        if (logEl && d?.battle_log) for (const e of d.battle_log) this._logText(logEl, e);
        this._onEnd();
    },
};

export default BattleView;
