import math
import random
import logging
from database import SessionLocal
from models import User, UserStat, Hero, Party, Item
from services.system.GameDataManager import GameDataManager
from services.system.ErrorCode import ErrorCode, error_response

logger = logging.getLogger("RPG_SERVER")

# ── 전투 상수 ──
BASE_HP_PER_VIT = 5
BASE_ATK_PER_STR = 2
BASE_MATK_PER_INT = 2
BASE_ACTION_SPEED = 10
ACTION_PER_AGI = 0.3
BASE_DEF_PER_VIT = 0.5
CRIT_BASE = 5
CRIT_PER_AGI = 0.5
ACTIVE_COOLDOWN = 4        # 액티브 스킬 쿨다운 (턴)
STATUS_TICK_DMG = 0.05     # 화상/독 틱 데미지 (최대HP%)

# ── 진영 시너지 ──
FACTION_SYNERGY = {
    "human_3":       {"label": "인간의 결속",  "desc": "전 스탯 +10%", "all_stat": 0.10},
    "demon_3":       {"label": "악마의 분노",  "desc": "공격력 +15%", "atk": 0.15},
    "celestial_3":   {"label": "천상의 가호",  "desc": "받는 피해 -15%", "dmg_reduction": 0.15},
    "mixed_3":       {"label": "삼계의 조화",  "desc": "전 스탯 +5%, 골드 +20%", "all_stat": 0.05, "gold_bonus": 0.20},
    "demon_human":   {"label": "지옥과 인간",  "desc": "치명타 +10%", "crit": 10},
    "celestial_demon": {"label": "빛과 어둠",  "desc": "스킬 데미지 +10%", "skill_dmg": 0.10},
    "celestial_human": {"label": "축복과 의지", "desc": "HP 회복 +15%", "hp_recovery": 0.15},
}

# ── 챕터 배경 정보 (CSV 없을 때 폴백) ──
CHAPTER_INFO = {
    1: {"sin": "분노", "name": "불타는 전장", "color": "#e03030"},
    2: {"sin": "질투", "name": "뒤틀린 숲", "color": "#30b050"},
    3: {"sin": "탐욕", "name": "황금 사막", "color": "#d0a020"},
    4: {"sin": "나태", "name": "망각의 동토", "color": "#808898"},
    5: {"sin": "폭식", "name": "심연의 동굴", "color": "#e07020"},
    6: {"sin": "색욕", "name": "타락한 궁전", "color": "#e03080"},
    7: {"sin": "교만", "name": "천상의 폐허", "color": "#8040e0"},
}

STAGE_NAMES = {1: "외곽 탐색", 2: "내부 침투", 3: "핵심부 돌파", 4: "보스전"}


class BattleManager:
    """3v3 파티 자동전투 시뮬레이션 (API 3xxx)"""

    @classmethod
    async def battle_start(cls, user_no: int, data: dict):
        """API 3001: 전투 시작"""
        stage_id = data.get("stage_id")
        if not stage_id:
            return error_response(ErrorCode.INVALID_REQUEST, "stage_id가 필요합니다.")

        stages = GameDataManager.REQUIRE_CONFIGS.get("stages", {})
        stage_meta = stages.get(stage_id) or stages.get(str(stage_id))
        if not stage_meta:
            return error_response(ErrorCode.STAGE_NOT_FOUND, f"스테이지 {stage_id}을(를) 찾을 수 없습니다.")

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.user_no == user_no).first()
            if not user:
                return error_response(ErrorCode.USER_NOT_FOUND, "유저를 찾을 수 없습니다.")
            stat = db.query(UserStat).filter(UserStat.user_no == user_no).first()
            if not stat:
                return error_response(ErrorCode.USER_NOT_FOUND, "유저 스탯 없음")
            party = db.query(Party).filter(Party.user_no == user_no).first()
            if not party:
                return error_response(ErrorCode.INVALID_REQUEST, "파티가 편성되지 않았습니다.")

            # 아군 유닛 생성
            allies, hero_list = [], []
            for slot_uid in [party.slot_1, party.slot_2, party.slot_3]:
                if slot_uid is None:
                    continue
                hero = db.query(Hero).filter(Hero.hero_uid == slot_uid, Hero.user_no == user_no).first()
                if hero:
                    hero_list.append(hero)
                    equips = db.query(Item).filter(
                        Item.user_no == user_no, Item.equipped_hero_uid == slot_uid, Item.is_equipped == True
                    ).all()
                    allies.append(cls._build_ally_unit(hero, stat, equips))

            if not allies:
                return error_response(ErrorCode.INVALID_REQUEST, "파티에 영웅이 없습니다.")

            # 진영 시너지
            synergy_info = cls._apply_faction_synergy(allies, hero_list)

            # 적 유닛 생성
            chapter = int(str(stage_id)[:1])
            stage_num = int(str(stage_id)[-1])
            is_boss_stage = stage_num == 4
            enemies = cls._build_enemies(stage_meta, chapter, is_boss_stage)

            # 스냅샷 (클라이언트 렌더링용)
            ally_snap = [{
                "name": u["name"], "max_hp": u["max_hp"], "side": "ally",
                "speed": round(u.get("speed", 10), 1),
                "faction": u.get("faction", "demon"), "grade": u.get("grade", "common"),
                "hero_id": u.get("hero_id", ""), "active_name": u.get("active_name", ""),
            } for u in allies]
            enemy_snap = [{
                "name": u["name"], "max_hp": u["max_hp"], "side": "enemy",
                "speed": round(u.get("speed", 10), 1),
                "is_boss": u.get("is_boss", False),
            } for u in enemies]

            # 스테이지 정보
            ch_info = CHAPTER_INFO.get(chapter, {})
            stage_info = {
                "chapter": chapter,
                "stage_num": stage_num,
                "stage_name": f"{chapter}-{stage_num}: {STAGE_NAMES.get(stage_num, '')}",
                "chapter_name": ch_info.get("name", ""),
                "sin": ch_info.get("sin", ""),
                "color": ch_info.get("color", "#e03030"),
            }

            # 전투 시뮬레이션
            battle_log, result = cls._simulate_battle(allies, enemies)

            # 보상
            rewards = {"exp": 0, "gold": 0}
            gold_bonus = sum(u.get("gold_bonus", 0) for u in allies)
            if result == "victory":
                rewards["exp"] = len(enemies) * 50 * chapter
                rewards["gold"] = int(len(enemies) * 30 * chapter * (1 + gold_bonus / 100))

                stat.exp += rewards["exp"]
                user.gold += rewards["gold"]

                level_config = GameDataManager.REQUIRE_CONFIGS.get("level_config", {})
                while True:
                    lv_data = level_config.get(stat.level)
                    if not lv_data:
                        break
                    if stat.exp >= lv_data.get("required_exp", stat.level * 1000):
                        stat.exp -= lv_data["required_exp"]
                        stat.level += 1
                        stat.stat_points += lv_data.get("stat_points", 5)
                    else:
                        break

                hero_exp = rewards["exp"] // max(len(hero_list), 1)
                for hero in hero_list:
                    hero.exp += hero_exp
                    while True:
                        lv_data = level_config.get(hero.level)
                        if not lv_data:
                            break
                        if hero.exp >= lv_data.get("required_exp", hero.level * 1000):
                            hero.exp -= lv_data["required_exp"]
                            hero.level += 1
                        else:
                            break

                if int(stage_id) >= user.current_stage:
                    user.current_stage = int(stage_id) + 1
                db.commit()

            return {
                "success": True,
                "message": "승리!" if result == "victory" else "패배...",
                "data": {
                    "result": result,
                    "stage": stage_info,
                    "synergy": synergy_info,
                    "allies": ally_snap,
                    "enemies": enemy_snap,
                    "battle_log": battle_log,
                    "rewards": rewards,
                    "user": {
                        "level": stat.level, "exp": stat.exp, "gold": user.gold,
                        "stat_points": stat.stat_points, "current_stage": user.current_stage,
                    },
                },
            }
        except Exception as e:
            db.rollback()
            logger.error(f"[BattleManager] battle_start 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "전투 처리 중 오류가 발생했습니다.")
        finally:
            db.close()

    # ══════════════════════════════════════════════
    # 유닛 빌드
    # ══════════════════════════════════════════════

    @classmethod
    def _build_ally_unit(cls, hero, user_stat, equips=None):
        hero_base = GameDataManager.REQUIRE_CONFIGS.get("hero_bases", {}).get(hero.hero_id, {})
        equip_map = GameDataManager.REQUIRE_CONFIGS.get("equip_base_map", {})
        is_baal = hero.hero_id == "baal"

        if is_baal:
            base_str, base_int, base_agi, base_vit, base_will = (
                user_stat.stat_str, user_stat.stat_int, user_stat.stat_agi,
                user_stat.stat_vit, user_stat.stat_will)
            lv = user_stat.level
        else:
            base_str = int(hero_base.get("base_str", 10))
            base_int = int(hero_base.get("base_int", 10))
            base_agi = int(hero_base.get("base_agi", 10))
            base_vit = int(hero_base.get("base_vit", 10))
            base_will = int(hero_base.get("base_will", 10))
            lv = hero.level

        total_str = base_str + lv * 2
        total_int = base_int + lv * 2
        total_agi = base_agi + lv * 2
        total_vit = base_vit + lv * 2

        equip_atk = equip_def = equip_agi = equip_will = 0
        if equips:
            for item in equips:
                base = equip_map.get(item.base_item_id, {})
                v = int(base.get("base_value", 0))
                st = base.get("base_stat", "")
                if st == "atk": equip_atk += v
                elif st == "def": equip_def += v
                elif st == "agi": equip_agi += v
                elif st == "will": equip_will += v

        skill_bonus = cls._calc_skill_tree_bonus(hero)
        will_bonus = 1.0 + user_stat.stat_will * 0.005 + equip_will * 0.003
        grade_mult = {"common": 1.0, "uncommon": 1.15, "rare": 1.3, "legendary": 1.5}
        mult = grade_mult.get(hero.grade, 1.0) * will_bonus

        hp = int(total_vit * BASE_HP_PER_VIT * mult * (1 + skill_bonus.get("hp_pct", 0) / 100))
        atk = int((total_str * BASE_ATK_PER_STR + equip_atk) * mult * (1 + skill_bonus.get("atk_pct", 0) / 100))
        matk = int(total_int * BASE_MATK_PER_INT * mult)
        defense = int((total_vit * BASE_DEF_PER_VIT + equip_def) * mult * (1 + skill_bonus.get("def_pct", 0) / 100))
        speed = BASE_ACTION_SPEED + (total_agi + equip_agi) * ACTION_PER_AGI
        crit = CRIT_BASE + total_agi * CRIT_PER_AGI + skill_bonus.get("crit", 0)
        final_atk = max(atk, matk)

        if is_baal:
            hp = int(hp * 1.05)
            final_atk = int(final_atk * 1.05)
            defense = int(defense * 1.05)

        return {
            "name": hero_base.get("hero_name", hero.hero_id),
            "hero_id": hero.hero_id,
            "side": "ally",
            "faction": hero.faction,
            "grade": hero.grade,
            "active_name": hero_base.get("active_name", ""),
            "active_desc": hero_base.get("active_desc", ""),
            "hp": hp, "max_hp": hp,
            "atk": final_atk, "defense": defense,
            "speed": speed, "crit": min(crit, 80),
            "action_gauge": 0, "alive": True,
            "lifesteal": skill_bonus.get("lifesteal", 0),
            "counter_chance": skill_bonus.get("counter_chance", 0),
            "dmg_reduction": skill_bonus.get("dmg_reduction", 0),
            "gold_bonus": skill_bonus.get("gold_bonus", 0),
            "atk_stack": skill_bonus.get("atk_stack", 0),
            "_atk_stacked": 0,
            "_active_cd": 0,        # 액티브 쿨다운 카운터
            "_statuses": [],         # [{"type": "burn"|"freeze"|"poison"|"charm", "turns": N}]
        }

    @classmethod
    def _build_enemies(cls, stage_meta, chapter=1, is_boss_stage=False):
        monsters = GameDataManager.REQUIRE_CONFIGS.get("monsters", {})
        waves = stage_meta.get("waves", {})
        enemies = []

        for wave_num, monster_idx in sorted(waves.items()):
            monster = monsters.get(int(monster_idx)) or monsters.get(str(monster_idx))
            if monster:
                enemies.append(cls._make_enemy_unit(monster, monster_idx, chapter))

        # 3v3: 적도 3체로 제한 (마지막 3체 — 보스가 마지막이므로)
        if len(enemies) > 3:
            enemies = enemies[-3:]

        if not enemies:
            ch_mult = 1 + (chapter - 1) * 0.4
            base_names = ["고블린 전사", "오크 돌격병", "스켈레톤 기사"] if not is_boss_stage else ["고블린 정예", "임프 마법사", "챕터 보스"]
            for i, nm in enumerate(base_names):
                is_boss = is_boss_stage and i == len(base_names) - 1
                hp_base = 200 if is_boss else 80
                atk_base = 25 if is_boss else 15
                enemies.append({
                    "name": nm, "side": "enemy", "is_boss": is_boss,
                    "hp": int(hp_base * ch_mult), "max_hp": int(hp_base * ch_mult),
                    "atk": int(atk_base * ch_mult), "defense": int(5 * ch_mult),
                    "speed": 12 if is_boss else 10, "crit": 10 if is_boss else 5,
                    "action_gauge": 0, "alive": True,
                    "lifesteal": 0, "counter_chance": 0,
                    "dmg_reduction": 0, "atk_stack": 0,
                    "_atk_stacked": 0, "_active_cd": 0, "_statuses": [],
                    "_phase": 1,
                })

        return enemies

    @staticmethod
    def _make_enemy_unit(monster, monster_idx, chapter):
        ch_mult = 1 + (chapter - 1) * 0.3
        return {
            "name": monster.get("name", f"몬스터#{monster_idx}"),
            "side": "enemy", "is_boss": False,
            "hp": int(float(monster.get("base_hp", 100)) * ch_mult),
            "max_hp": int(float(monster.get("base_hp", 100)) * ch_mult),
            "atk": int(float(monster.get("base_atk", 20)) * ch_mult),
            "defense": int(float(monster.get("base_def", 5)) * ch_mult),
            "speed": 10 + float(monster.get("atk_speed", 1.0)) * 3,
            "crit": 5, "action_gauge": 0, "alive": True,
            "lifesteal": 0, "counter_chance": 0,
            "dmg_reduction": 0, "atk_stack": 0,
            "_atk_stacked": 0, "_active_cd": 0, "_statuses": [],
            "_phase": 1,
        }

    # ══════════════════════════════════════════════
    # 시너지
    # ══════════════════════════════════════════════

    @classmethod
    def _apply_faction_synergy(cls, allies, hero_list):
        factions = [h.faction for h in hero_list]
        faction_set = set(factions)
        synergy = None
        syn_key = None

        if len(factions) >= 2:
            if len(faction_set) == 1:
                syn_key = f"{factions[0]}_3"
            elif len(faction_set) == len(factions) and len(factions) == 3:
                syn_key = "mixed_3"
            elif len(faction_set) == 2:
                syn_key = "_".join(sorted(faction_set))

        synergy = FACTION_SYNERGY.get(syn_key) if syn_key else None
        if not synergy:
            return None

        for unit in allies:
            if "all_stat" in synergy:
                m = synergy["all_stat"]
                unit["hp"] = int(unit["hp"] * (1 + m))
                unit["max_hp"] = int(unit["max_hp"] * (1 + m))
                unit["atk"] = int(unit["atk"] * (1 + m))
                unit["defense"] = int(unit["defense"] * (1 + m))
            if "atk" in synergy:
                unit["atk"] = int(unit["atk"] * (1 + synergy["atk"]))
            if "dmg_reduction" in synergy:
                unit["dmg_reduction"] = unit.get("dmg_reduction", 0) + synergy["dmg_reduction"] * 100
            if "crit" in synergy:
                unit["crit"] = min(80, unit["crit"] + synergy["crit"])
            if "gold_bonus" in synergy:
                unit["gold_bonus"] = unit.get("gold_bonus", 0) + synergy["gold_bonus"] * 100

        return {"label": synergy["label"], "desc": synergy["desc"]}

    # ══════════════════════════════════════════════
    # 스킬트리 보너스
    # ══════════════════════════════════════════════

    @classmethod
    def _calc_skill_tree_bonus(cls, hero):
        bonus = {
            "atk_pct": 0, "def_pct": 0, "crit": 0, "hp_pct": 0,
            "lifesteal": 0, "counter_chance": 0, "dmg_reduction": 0,
            "gold_bonus": 0, "atk_stack": 0,
        }
        skill_trees = GameDataManager.REQUIRE_CONFIGS.get("skill_trees", {})

        for tree_num in [1, 2]:
            tree_id = hero.skill_tree_1 if tree_num == 1 else hero.skill_tree_2
            points = dict(hero.tree1_points or {}) if tree_num == 1 else dict(hero.tree2_points or {})

            for sk in skill_trees.get(tree_id, []):
                lv = points.get(sk.get("skill_id"), 0)
                if lv <= 0:
                    continue
                etype = sk.get("effect_type", "")
                val = float(sk.get("effect_base", 0)) + float(sk.get("effect_per_level", 0)) * (lv - 1)

                if etype == "lifesteal": bonus["lifesteal"] += val
                elif etype == "crit_up": bonus["crit"] += val
                elif etype == "def_up": bonus["def_pct"] += val
                elif etype == "dmg_reduction": bonus["dmg_reduction"] += val
                elif etype == "counter_atk": bonus["counter_chance"] += val
                elif etype in ("gold_bonus", "drop_bonus"): bonus["gold_bonus"] += val
                elif etype == "atk_stack": bonus["atk_stack"] += val
                elif etype == "team_stat_up":
                    bonus["atk_pct"] += val; bonus["def_pct"] += val; bonus["hp_pct"] += val

        return bonus

    # ══════════════════════════════════════════════
    # 전투 시뮬레이션 (풀 버전)
    # ══════════════════════════════════════════════

    @classmethod
    def _simulate_battle(cls, allies, enemies, max_turns=60):
        all_units = allies + enemies
        log = []
        turn = 0

        while turn < max_turns:
            turn += 1

            # ── 상태이상 틱 (턴 시작) ──
            for u in all_units:
                if not u["alive"]:
                    continue
                new_statuses = []
                for st in u.get("_statuses", []):
                    if st["type"] == "freeze":
                        # 동결: 이번 턴 행동 불가
                        u["_frozen_this_turn"] = True
                        st["turns"] -= 1
                        if st["turns"] > 0:
                            new_statuses.append(st)
                        log.append({"turn": turn, "type": "status_tick", "target": u["name"],
                                    "status": "freeze", "value": 0})
                    elif st["type"] in ("burn", "poison"):
                        tick_dmg = max(1, int(u["max_hp"] * STATUS_TICK_DMG))
                        u["hp"] = max(0, u["hp"] - tick_dmg)
                        st["turns"] -= 1
                        if st["turns"] > 0:
                            new_statuses.append(st)
                        log.append({"turn": turn, "type": "status_tick", "target": u["name"],
                                    "status": st["type"], "value": tick_dmg, "target_hp": u["hp"]})
                        if u["hp"] <= 0:
                            u["alive"] = False
                    elif st["type"] == "charm":
                        st["turns"] -= 1
                        if st["turns"] > 0:
                            new_statuses.append(st)
                        log.append({"turn": turn, "type": "status_tick", "target": u["name"],
                                    "status": "charm", "value": 0})
                    else:
                        st["turns"] -= 1
                        if st["turns"] > 0:
                            new_statuses.append(st)
                u["_statuses"] = new_statuses

                if not u["alive"]:
                    if not any(e["alive"] for e in enemies):
                        return log, "victory"
                    if not any(a["alive"] for a in allies):
                        return log, "defeat"

            # ── 행동 게이지 충전 ──
            for u in all_units:
                if u["alive"] and not u.get("_frozen_this_turn"):
                    u["action_gauge"] += u["speed"]
                u["_frozen_this_turn"] = False  # 리셋

            actors = sorted(
                [u for u in all_units if u["alive"] and u["action_gauge"] >= 100],
                key=lambda u: u["action_gauge"], reverse=True
            )

            for actor in actors:
                if not actor["alive"]:
                    continue
                actor["action_gauge"] -= 100

                # 매혹 상태 → 같은 편 공격
                charmed = any(s["type"] == "charm" for s in actor.get("_statuses", []))

                if actor["side"] == "ally":
                    targets = [u for u in (allies if charmed else enemies) if u["alive"] and u is not actor]
                else:
                    targets = [u for u in (enemies if charmed else allies) if u["alive"] and u is not actor]

                if not targets:
                    continue

                target = min(targets, key=lambda t: t["hp"])

                # ── 액티브 스킬 체크 ──
                used_skill = False
                skill_name = ""
                actor["_active_cd"] = max(0, actor.get("_active_cd", 0) - 1)

                if actor.get("_active_cd", 0) <= 0 and actor.get("active_name"):
                    used_skill = True
                    skill_name = actor["active_name"]
                    actor["_active_cd"] = ACTIVE_COOLDOWN
                    skill_mult = 2.0  # 액티브 = 기본 2배 데미지

                    # 스킬 부가효과 (hero_id 기반)
                    status_to_apply = cls._get_skill_status(actor.get("hero_id", ""))
                else:
                    skill_mult = 1.0
                    status_to_apply = None

                # ── 누적 공격력 ──
                stack = actor.get("atk_stack", 0)
                if stack > 0:
                    actor["_atk_stacked"] += stack
                effective_atk = int(actor["atk"] * (1 + actor.get("_atk_stacked", 0) / 100))

                # ── 데미지 계산 ──
                is_crit = random.random() * 100 < actor["crit"]
                raw_dmg = max(1, int(effective_atk * skill_mult) - target["defense"])
                if is_crit:
                    raw_dmg = int(raw_dmg * 1.5)

                reduction = target.get("dmg_reduction", 0)
                if reduction > 0:
                    raw_dmg = max(1, int(raw_dmg * (1 - reduction / 100)))

                target["hp"] = max(0, target["hp"] - raw_dmg)

                entry = {
                    "turn": turn,
                    "type": "skill" if used_skill else "attack",
                    "actor": actor["name"],
                    "target": target["name"],
                    "damage": raw_dmg,
                    "crit": is_crit,
                    "target_hp": target["hp"],
                }
                if used_skill:
                    entry["skill_name"] = skill_name
                log.append(entry)

                # ── 스킬 상태이상 부여 ──
                if status_to_apply and target["alive"]:
                    if random.random() * 100 < status_to_apply.get("chance", 30):
                        target["_statuses"].append({
                            "type": status_to_apply["type"],
                            "turns": status_to_apply.get("turns", 2),
                        })
                        log.append({
                            "turn": turn, "type": "status_apply",
                            "actor": actor["name"], "target": target["name"],
                            "status": status_to_apply["type"],
                            "turns": status_to_apply.get("turns", 2),
                        })

                # ── 흡혈 ──
                ls = actor.get("lifesteal", 0)
                if ls > 0 and actor["alive"]:
                    heal = int(raw_dmg * ls / 100)
                    if heal > 0:
                        actor["hp"] = min(actor["max_hp"], actor["hp"] + heal)
                        log.append({
                            "turn": turn, "type": "lifesteal",
                            "actor": actor["name"], "value": heal,
                            "actor_hp": actor["hp"],
                        })

                # ── 반격 ──
                if target["alive"] and target.get("counter_chance", 0) > 0:
                    if random.random() * 100 < target["counter_chance"]:
                        counter_dmg = max(1, target["atk"] // 2 - actor["defense"])
                        actor["hp"] = max(0, actor["hp"] - counter_dmg)
                        log.append({
                            "turn": turn, "type": "counter",
                            "actor": target["name"], "target": actor["name"],
                            "damage": counter_dmg, "target_hp": actor["hp"],
                        })
                        if actor["hp"] <= 0:
                            actor["alive"] = False

                if target["hp"] <= 0:
                    target["alive"] = False

                # ── 보스 페이즈 전환 ──
                for u in enemies:
                    if u.get("is_boss") and u["alive"]:
                        hp_pct = u["hp"] / u["max_hp"]
                        phase = u.get("_phase", 1)
                        if phase == 1 and hp_pct <= 0.5:
                            u["_phase"] = 2
                            u["atk"] = int(u["atk"] * 1.3)
                            u["speed"] += 2
                            log.append({"turn": turn, "type": "phase", "actor": u["name"],
                                        "phase": 2, "message": f"{u['name']} — 2페이즈 각성!"})
                        elif phase == 2 and hp_pct <= 0.2:
                            u["_phase"] = 3
                            u["atk"] = int(u["atk"] * 1.5)
                            u["crit"] = min(80, u["crit"] + 20)
                            log.append({"turn": turn, "type": "phase", "actor": u["name"],
                                        "phase": 3, "message": f"{u['name']} — 최종 페이즈!"})

                # ── 승패 체크 ──
                if not any(e["alive"] for e in enemies):
                    return log, "victory"
                if not any(a["alive"] for a in allies):
                    return log, "defeat"

        return log, "defeat"

    @staticmethod
    def _get_skill_status(hero_id):
        """영웅별 액티브 스킬의 상태이상 부여 효과"""
        table = {
            "satan": {"type": "burn", "chance": 40, "turns": 3},
            "moloch": {"type": "burn", "chance": 50, "turns": 3},
            "seraphim": {"type": "burn", "chance": 35, "turns": 2},
            "astaroth": {"type": "freeze", "chance": 30, "turns": 2},
            "yukionna": {"type": "freeze", "chance": 40, "turns": 2},
            "pazuzu": {"type": "freeze", "chance": 25, "turns": 2},
            "asmodeus": {"type": "charm", "chance": 30, "turns": 2},
            "incubus": {"type": "charm", "chance": 35, "turns": 2},
            "samael": {"type": "poison", "chance": 40, "turns": 3},
            "lilith": {"type": "poison", "chance": 30, "turns": 3},
        }
        return table.get(hero_id)
