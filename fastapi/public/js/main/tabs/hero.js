/**
 * TheSevenTactics — Hero Tab
 * 보유 영웅 목록 + 상세 + 스킬트리 투자
 */
import { apiCall } from '../../api.js';
import { showToast } from '../../utils.js';

const FACTION_ICON = { human: '🧑', demon: '😈', celestial: '👼' };
const GRADE_CLASS = { common: 'grade-common', uncommon: 'grade-uncommon', rare: 'grade-rare', legendary: 'grade-legendary' };

const HeroTab = {
    el: null,
    _heroes: [],
    _selected: null,

    mount(el) {
        this.el = el;
        el.innerHTML = '<div class="hero-tab"><div class="hero-empty">로딩 중...</div></div>';
        this._load();
    },

    unmount() {},

    async _load() {
        const result = await apiCall(4001, {});
        if (result?.success) {
            this._heroes = result.data.heroes || [];
            this._render();
        }
    },

    _render() {
        if (!this._heroes.length) {
            this.el.innerHTML = '<div class="hero-tab"><div class="hero-empty">보유한 영웅이 없습니다</div></div>';
            return;
        }

        let html = '<div class="hero-tab"><div class="hero-list">';
        for (const h of this._heroes) {
            const icon = FACTION_ICON[h.faction] || '❓';
            const cls = GRADE_CLASS[h.grade] || '';
            const sel = this._selected === h.hero_uid ? ' selected' : '';
            html += `
                <div class="hero-card${sel}" data-action="select-hero" data-uid="${h.hero_uid}">
                    <div class="hero-card-icon">${icon}</div>
                    <div class="hero-card-info">
                        <div class="hero-card-name ${cls}">${h.hero_name}</div>
                        <div class="hero-card-meta">Lv.${h.level} · ${h.grade} · ${h.faction}</div>
                    </div>
                </div>`;
        }
        html += '</div><div id="hero-detail-area"></div></div>';
        this.el.innerHTML = html;

        this.el.addEventListener('pointerdown', (e) => {
            const card = e.target.closest('[data-action="select-hero"]');
            if (card) {
                this._selected = parseInt(card.dataset.uid);
                this._loadDetail(this._selected);
            }
            const investBtn = e.target.closest('[data-action="invest-skill"]');
            if (investBtn) {
                this._investSkill(
                    parseInt(investBtn.dataset.heroUid),
                    parseInt(investBtn.dataset.treeNum),
                    investBtn.dataset.skillId
                );
            }
        });

        if (this._selected) this._loadDetail(this._selected);
    },

    async _loadDetail(heroUid) {
        const result = await apiCall(4002, { hero_uid: heroUid });
        if (!result?.success) return;

        const d = result.data;
        const area = this.el.querySelector('#hero-detail-area');
        if (!area) return;

        let html = `<div class="hero-detail">
            <div class="hero-detail-header">${d.hero_name} (${d.grade})</div>
            <div class="hero-detail-row"><span>진영</span><span class="val">${d.faction}</span></div>
            <div class="hero-detail-row"><span>STR</span><span class="val">${d.base_stats.str}</span></div>
            <div class="hero-detail-row"><span>INT</span><span class="val">${d.base_stats.int}</span></div>
            <div class="hero-detail-row"><span>DEX</span><span class="val">${d.base_stats.dex}</span></div>
            <div class="hero-detail-row"><span>VIT</span><span class="val">${d.base_stats.vit}</span></div>
            <div class="hero-detail-row"><span>LCK</span><span class="val">${d.base_stats.lck}</span></div>`;

        if (d.passive_name) {
            html += `<div class="hero-detail-row"><span>패시브</span><span class="val">${d.passive_name}</span></div>`;
        }
        if (d.active_name) {
            html += `<div class="hero-detail-row"><span>액티브</span><span class="val">${d.active_name}</span></div>`;
        }

        // 스킬트리
        for (const treeNum of [1, 2]) {
            const treeKey = `tree${treeNum}`;
            const treeId = d[`skill_tree_${treeNum}`];
            const skills = d.skill_trees[treeKey] || [];
            const points = d[`tree${treeNum}_points`] || {};

            html += `<div class="hero-detail-section">
                <div class="hero-detail-section-title">${treeId.toUpperCase()} 트리</div>`;

            for (const sk of skills) {
                const curLv = points[sk.skill_id] || 0;
                const maxLv = parseInt(sk.max_level || 5);
                html += `<div class="hero-skill-row">
                    <span class="hero-skill-name">${sk.skill_name}</span>
                    <span>
                        <span class="hero-skill-level">${curLv}/${maxLv}</span>
                        ${curLv < maxLv ? `<button class="btn" style="padding:0 4px;min-height:20px;font-size:9px;margin-left:4px"
                            data-action="invest-skill" data-hero-uid="${d.hero_uid}" data-tree-num="${treeNum}" data-skill-id="${sk.skill_id}">+</button>` : ''}
                    </span>
                </div>`;
            }
            html += '</div>';
        }

        html += '</div>';
        area.innerHTML = html;
    },

    async _investSkill(heroUid, treeNum, skillId) {
        const result = await apiCall(4003, { hero_uid: heroUid, tree_num: treeNum, skill_id: skillId });
        if (result?.success) {
            showToast(result.message, 'success');
            this._loadDetail(heroUid);
        }
    },
};

export default HeroTab;
