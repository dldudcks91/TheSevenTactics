"""
TheSevenTactics — StatusEffectManager
7대 죄악 대응 상태이상 7종 관리

| 효과 | 죄종 | 설명 |
|------|------|------|
| burn | 분노 | 틱 데미지 + 힐 감소 50% |
| poison | 질투 | 틱 데미지 |
| stun | 탐욕 | 행동 불가 (1턴) |
| freeze | 나태 | 행동속도 50% 감소 |
| corrode | 폭식 | 방어력 영구 감소 (스택) |
| charm | 색욕 | 아군 공격 |
| judge | 교만 | 스킬 사용 불가 |
"""
import logging

logger = logging.getLogger("RPG_SERVER")

# ── 상태이상 정의 ──
STATUS_DEFS = {
    "burn":    {"duration": 3, "sin": "wrath",    "stackable": False, "desc": "화상: 틱 데미지 + 힐 감소"},
    "poison":  {"duration": 3, "sin": "envy",     "stackable": False, "desc": "중독: 틱 데미지"},
    "stun":    {"duration": 1, "sin": "greed",    "stackable": False, "desc": "기절: 행동 불가"},
    "freeze":  {"duration": 2, "sin": "sloth",    "stackable": False, "desc": "빙결: 행동속도 50% 감소"},
    "corrode": {"duration": 99, "sin": "gluttony", "stackable": True,  "desc": "침식: 방어력 영구 감소"},
    "charm":   {"duration": 2, "sin": "lust",     "stackable": False, "desc": "매혹: 아군 공격"},
    "judge":   {"duration": 2, "sin": "pride",    "stackable": False, "desc": "심판: 스킬 사용 불가"},
}

# 틱 데미지 비율 (최대 HP 대비)
TICK_DMG_RATIO = 0.05
# 침식 방어력 감소 (스택당)
CORRODE_DEF_REDUCTION = 0.02


class StatusEffectManager:
    """상태이상 적용/틱/해제를 관리하는 유틸리티"""

    @staticmethod
    def apply_status(unit, effect_type, duration=None, chance=100):
        """
        유닛에 상태이상 적용.
        Returns: True if applied, False if resisted/invalid
        """
        import random
        if not unit.get("alive", True):
            return False

        if random.random() * 100 >= chance:
            return False

        sdef = STATUS_DEFS.get(effect_type)
        if not sdef:
            return False

        dur = duration if duration is not None else sdef["duration"]
        statuses = unit.setdefault("_statuses", [])

        if sdef["stackable"]:
            # corrode: 스택 추가
            existing = next((s for s in statuses if s["type"] == effect_type), None)
            if existing:
                existing["stacks"] = existing.get("stacks", 1) + 1
            else:
                statuses.append({"type": effect_type, "turns": dur, "stacks": 1})
            # 방어력 즉시 감소
            base_def = unit.get("_base_defense", unit.get("defense", 0))
            unit.setdefault("_base_defense", base_def)
            total_stacks = sum(s.get("stacks", 0) for s in statuses if s["type"] == "corrode")
            unit["defense"] = max(0, int(base_def * (1 - total_stacks * CORRODE_DEF_REDUCTION)))
        else:
            # 비스택: 갱신 (이미 있으면 duration만 리셋)
            existing = next((s for s in statuses if s["type"] == effect_type), None)
            if existing:
                existing["turns"] = dur
            else:
                statuses.append({"type": effect_type, "turns": dur})

        return True

    @staticmethod
    def tick_statuses(unit, log, turn):
        """
        턴 시작 시 모든 상태이상 틱 처리.
        Returns: set of active effect types (for behavior modification)
        """
        if not unit.get("alive", True):
            return set()

        active_effects = set()
        new_statuses = []

        for st in unit.get("_statuses", []):
            etype = st["type"]

            if etype == "stun":
                active_effects.add("stun")
                st["turns"] -= 1
                if st["turns"] > 0:
                    new_statuses.append(st)
                log.append({"turn": turn, "type": "status_tick", "target": unit["name"],
                            "status": "stun", "value": 0})

            elif etype == "freeze":
                active_effects.add("freeze")
                st["turns"] -= 1
                if st["turns"] > 0:
                    new_statuses.append(st)
                log.append({"turn": turn, "type": "status_tick", "target": unit["name"],
                            "status": "freeze", "value": 0})

            elif etype in ("burn", "poison"):
                active_effects.add(etype)
                tick_dmg = max(1, int(unit["max_hp"] * TICK_DMG_RATIO))
                unit["hp"] = max(0, unit["hp"] - tick_dmg)
                st["turns"] -= 1
                if st["turns"] > 0:
                    new_statuses.append(st)
                log.append({"turn": turn, "type": "status_tick", "target": unit["name"],
                            "status": etype, "value": tick_dmg, "target_hp": unit["hp"]})
                if unit["hp"] <= 0:
                    unit["alive"] = False

            elif etype == "charm":
                active_effects.add("charm")
                st["turns"] -= 1
                if st["turns"] > 0:
                    new_statuses.append(st)
                log.append({"turn": turn, "type": "status_tick", "target": unit["name"],
                            "status": "charm", "value": 0})

            elif etype == "judge":
                active_effects.add("judge")
                st["turns"] -= 1
                if st["turns"] > 0:
                    new_statuses.append(st)
                log.append({"turn": turn, "type": "status_tick", "target": unit["name"],
                            "status": "judge", "value": 0})

            elif etype == "corrode":
                active_effects.add("corrode")
                # corrode는 영구 — turns 감소 안 함
                new_statuses.append(st)

            else:
                st["turns"] -= 1
                if st["turns"] > 0:
                    new_statuses.append(st)

        unit["_statuses"] = new_statuses
        return active_effects

    @staticmethod
    def has_status(unit, effect_type):
        return any(s["type"] == effect_type for s in unit.get("_statuses", []))

    @staticmethod
    def can_act(unit):
        """stun/freeze 여부로 행동 가능 여부 판단"""
        for s in unit.get("_statuses", []):
            if s["type"] == "stun":
                return False
        return True

    @staticmethod
    def is_skill_blocked(unit):
        """judge 상태이면 스킬 사용 불가"""
        return any(s["type"] == "judge" for s in unit.get("_statuses", []))

    @staticmethod
    def get_speed_modifier(unit):
        """freeze 상태이면 속도 50% 감소"""
        if any(s["type"] == "freeze" for s in unit.get("_statuses", [])):
            return 0.5
        return 1.0

    @staticmethod
    def is_charmed(unit):
        return any(s["type"] == "charm" for s in unit.get("_statuses", []))

    @staticmethod
    def has_heal_reduction(unit):
        """burn 상태이면 힐 50% 감소"""
        return any(s["type"] == "burn" for s in unit.get("_statuses", []))
