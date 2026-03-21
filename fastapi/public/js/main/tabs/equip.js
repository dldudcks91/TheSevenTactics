/**
 * TheSevenTactics — Equipment Tab (3부위: weapon/armor/accessory)
 * 영웅별 장비 장착/해제 + 인벤토리 + 판매
 */
import { apiCall } from '../../api.js';
import { showToast } from '../../utils.js';

const SLOT_LABEL = {
    weapon: '무기', armor: '갑옷', accessory: '장신구',
};
const SLOT_ORDER = ['weapon', 'armor', 'accessory'];
const RARITY_COLOR = { magic: '#6688ff', rare: '#ffcc00', craft: '#ff6600', unique: '#ff44aa' };

const EquipTab = {
    el: null,
    _heroes: [],
    _items: [],
    _selectedHeroUid: null,
    _handleEvent: null,

    mount(el) {
        this.el = el;
        el.innerHTML = '<div class="equip-tab"><div class="equip-empty">로딩 중...</div></div>';
        this._handleEvent = this._onEvent.bind(this);
        el.addEventListener('pointerdown', this._handleEvent);
        this._load();
    },

    unmount() {
        if (this._handleEvent) {
            this.el.removeEventListener('pointerdown', this._handleEvent);
        }
    },

    async _load() {
        const [heroRes, invRes] = await Promise.all([
            apiCall(4001, {}),
            apiCall(2001, {}),
        ]);
        if (heroRes?.success) this._heroes = heroRes.data.heroes || [];
        if (invRes?.success) this._items = invRes.data.items || [];

        if (this._heroes.length && !this._selectedHeroUid) {
            this._selectedHeroUid = this._heroes[0].hero_uid;
        }
        this._render();
    },

    _render() {
        if (!this._heroes.length) {
            this.el.innerHTML = '<div class="equip-tab"><div class="equip-empty">보유한 영웅이 없습니다</div></div>';
            return;
        }

        let html = '<div class="equip-tab">';

        // 영웅 선택
        html += '<div class="equip-hero-select">';
        for (const h of this._heroes) {
            const active = h.hero_uid === this._selectedHeroUid ? ' active' : '';
            html += `<button class="equip-hero-btn${active}" data-action="pick-hero" data-uid="${h.hero_uid}">${h.hero_name}</button>`;
        }
        html += '</div>';

        // 3부위 장착 슬롯
        const equipped = this._items.filter(it => it.is_equipped && it.equipped_hero_uid === this._selectedHeroUid);
        const equippedBySlot = {};
        for (const it of equipped) equippedBySlot[it.equip_slot || it.main_group] = it;

        html += '<div class="equip-slots">';
        for (const slot of SLOT_ORDER) {
            const it = equippedBySlot[slot];
            if (it) {
                const color = RARITY_COLOR[it.rarity] || '#aaa';
                const statText = it.min_damage > 0
                    ? `DMG ${it.min_damage}~${it.max_damage}`
                    : `DEF ${it.base_defense}`;
                html += `<div class="equip-slot-card filled" data-action="unequip" data-item-uid="${it.item_uid}" style="border-color:${color}">
                    <div class="equip-slot-label">${SLOT_LABEL[slot]}</div>
                    <div class="equip-slot-name" style="color:${color}">${it.item_name}</div>
                    <div class="equip-slot-stat">${statText}</div>
                    <div class="equip-slot-rarity">${it.rarity} iLv${it.item_level}</div>
                </div>`;
            } else {
                html += `<div class="equip-slot-card">
                    <div class="equip-slot-label">${SLOT_LABEL[slot]}</div>
                    <div class="equip-slot-empty">— 비어있음 —</div>
                </div>`;
            }
        }
        html += '</div>';

        // 인벤토리
        html += '<div class="equip-inv-title">인벤토리</div>';
        const unequipped = this._items.filter(it => !it.is_equipped);
        if (unequipped.length) {
            html += '<div class="equip-inv-list">';
            for (const it of unequipped) {
                const color = RARITY_COLOR[it.rarity] || '#aaa';
                const slotName = SLOT_LABEL[it.main_group] || it.main_group;
                const statText = it.min_damage > 0
                    ? `DMG ${it.min_damage}~${it.max_damage}`
                    : `DEF ${it.base_defense}`;
                html += `<div class="equip-inv-item">
                    <div class="equip-inv-info">
                        <div class="equip-inv-name" style="color:${color}">${it.item_name}</div>
                        <div class="equip-inv-meta">${slotName} · ${statText} · iLv${it.item_level}</div>
                        ${it.prefix_id ? `<div class="equip-inv-affix">접두: ${it.prefix_id}</div>` : ''}
                        ${it.suffix_id ? `<div class="equip-inv-affix">접미: ${it.suffix_id}</div>` : ''}
                    </div>
                    <div class="equip-inv-actions">
                        <button class="equip-action-btn" data-action="equip" data-item-uid="${it.item_uid}">장착</button>
                        <button class="equip-action-btn sell" data-action="sell" data-item-uid="${it.item_uid}">판매</button>
                    </div>
                </div>`;
            }
            html += '</div>';
        } else {
            html += '<div class="equip-empty">인벤토리가 비어있습니다</div>';
        }

        html += '</div>';
        this.el.innerHTML = html;
    },

    _onEvent(e) {
        const pick = e.target.closest('[data-action="pick-hero"]');
        if (pick) {
            const uid = parseInt(pick.dataset.uid);
            if (uid !== this._selectedHeroUid) {
                this._selectedHeroUid = uid;
                this._render();
            }
            return;
        }

        const equip = e.target.closest('[data-action="equip"]');
        if (equip) {
            this._equipItem(equip.dataset.itemUid);
            return;
        }

        const unequip = e.target.closest('[data-action="unequip"]');
        if (unequip) {
            this._unequipItem(unequip.dataset.itemUid);
            return;
        }

        const sell = e.target.closest('[data-action="sell"]');
        if (sell) {
            this._sellItem(sell.dataset.itemUid);
        }
    },

    async _equipItem(itemUid) {
        const result = await apiCall(2002, { item_uid: itemUid, hero_uid: this._selectedHeroUid });
        if (result?.success) {
            showToast(result.message, 'success');
            await this._refreshInventory();
        }
    },

    async _unequipItem(itemUid) {
        const result = await apiCall(2003, { item_uid: itemUid });
        if (result?.success) {
            showToast(result.message, 'success');
            await this._refreshInventory();
        }
    },

    async _sellItem(itemUid) {
        const result = await apiCall(2004, { item_uid: itemUid });
        if (result?.success) {
            showToast(result.message, 'success');
            await this._refreshInventory();
        }
    },

    async _refreshInventory() {
        const res = await apiCall(2001, {});
        if (res?.success) {
            this._items = res.data.items || [];
            this._render();
        }
    },
};

export default EquipTab;
