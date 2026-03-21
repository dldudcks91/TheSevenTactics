import uuid
import random
import logging
from services.system.GameDataManager import GameDataManager
from services.rpg.EquipmentManager import remap_slot

logger = logging.getLogger("RPG_SERVER")


class ItemDropManager:
    """
    mlvl 기반 아이템 드롭 생성
    D2 구조: dlvl → mlvl → ilvl
    """

    # 스폰 등급별 드롭 판정 횟수
    GRADE_ROLL_COUNT = {
        "normal": 1,
        "elite": 2,
        "stage_boss": 3,
        "chapter_boss": 5,
    }

    # 등급별 mlvl 보정
    GRADE_MLVL_BONUS = {
        "normal": 0,
        "elite": 2,
        "stage_boss": 3,
        "chapter_boss": 0,  # 고정값 사용
    }

    # 등급 확률 (mlvl 기반, 기본값)
    @classmethod
    def _get_rarity_weights(cls, mlvl):
        """mlvl에 따른 장비 등급 드롭 확률"""
        # mlvl이 높을수록 상위 등급 확률 상승
        magic_w = max(50, 100 - mlvl * 1.5)
        rare_w = min(35, 5 + mlvl * 0.8)
        unique_w = min(5, mlvl * 0.1)
        return {
            "magic": magic_w,
            "rare": rare_w,
            "unique": unique_w,
        }

    @classmethod
    def generate_drops(cls, monsters_killed, dlvl, chapter=1, spawn_grade="normal"):
        """
        전투 승리 후 드롭 아이템 목록 생성

        Args:
            monsters_killed: 처치한 몬스터 목록 [{monster_idx, name, ...}]
            dlvl: 던전 레벨
            chapter: 챕터 번호 (죄종 편향용)
            spawn_grade: 스폰 등급 (normal/elite/stage_boss/chapter_boss)

        Returns:
            {"gold": int, "items": [item_dict, ...], "exp": int}
        """
        total_gold = 0
        total_exp = 0
        items = []

        equip_bases = GameDataManager.REQUIRE_CONFIGS.get("equip_bases", [])
        prefixes = GameDataManager.REQUIRE_CONFIGS.get("prefixes", [])
        suffixes = GameDataManager.REQUIRE_CONFIGS.get("suffixes", [])

        for m in monsters_killed:
            mlvl_bonus = cls.GRADE_MLVL_BONUS.get(spawn_grade, 0)
            mlvl = dlvl + mlvl_bonus

            # 골드 드롭
            base_gold = int(m.get("exp_reward", 10) * 0.5)
            gold_mult = {"normal": 1.0, "elite": 2.0, "stage_boss": 5.0, "chapter_boss": 10.0}
            total_gold += int(base_gold * gold_mult.get(spawn_grade, 1.0))

            # 경험치
            exp_mult = {"normal": 1.0, "elite": 3.0, "stage_boss": 10.0, "chapter_boss": 20.0}
            total_exp += int(m.get("exp_reward", 10) * exp_mult.get(spawn_grade, 1.0))

            # 장비 드롭 판정
            roll_count = cls.GRADE_ROLL_COUNT.get(spawn_grade, 1)
            for _ in range(roll_count):
                if random.random() < cls._drop_chance(spawn_grade):
                    item = cls._generate_equipment(mlvl, chapter, equip_bases, prefixes, suffixes)
                    if item:
                        items.append(item)

        return {
            "gold": total_gold,
            "exp": total_exp,
            "items": items,
        }

    @classmethod
    def _drop_chance(cls, spawn_grade):
        """등급별 장비 드롭 확률"""
        chances = {
            "normal": 0.08,       # 8%
            "elite": 0.25,        # 25%
            "stage_boss": 0.60,   # 60%
            "chapter_boss": 0.90, # 90%
        }
        return chances.get(spawn_grade, 0.05)

    @classmethod
    def _generate_equipment(cls, mlvl, chapter, equip_bases, prefixes, suffixes):
        """단일 장비 아이템 생성"""
        if not equip_bases:
            return None

        # 1. 베이스 선택 (39개 중 랜덤)
        base = random.choice(equip_bases)

        # 2. 등급 결정
        weights = cls._get_rarity_weights(mlvl)
        rarity = random.choices(
            list(weights.keys()),
            weights=list(weights.values()),
            k=1
        )[0]

        # 3. 접두/접미사 결정 (등급에 따라)
        prefix_id = None
        suffix_id = None

        slot_type = base.get("main_group", "weapon")
        slot_prefixes = [p for p in prefixes if p.get("equipment_type", "") == slot_type]
        slot_suffixes = [s for s in suffixes if s.get("equipment_type", "") == slot_type]

        if rarity == "magic":
            # 매직: 접두 or 접미 1개
            if slot_prefixes and random.random() < 0.5:
                prefix_id = random.choice(slot_prefixes).get("prefix", "")
            elif slot_suffixes:
                suffix_id = random.choice(slot_suffixes).get("suffix", "")
        elif rarity in ("rare", "craft"):
            # 레어/크래프트: 접두1 + 접미1
            if slot_prefixes:
                prefix_id = random.choice(slot_prefixes).get("prefix", "")
            if slot_suffixes:
                suffix_id = random.choice(slot_suffixes).get("suffix", "")

        # 4. 동적 옵션 (접사 수치)
        dynamic_options = {}
        if prefix_id:
            prefix_data = next((p for p in prefixes if p.get("prefix") == prefix_id and p.get("equipment_type") == slot_type), None)
            if prefix_data:
                stat1 = prefix_data.get("stat_1", "")
                if stat1 and stat1 != "-":
                    min_v = float(prefix_data.get("min_stat_1", 0))
                    max_v = float(prefix_data.get("max_stat_1", 0))
                    # ilvl 기반 수치 제한
                    ilvl_ratio = min(1.0, mlvl / 50.0)
                    actual_max = min_v + (max_v - min_v) * ilvl_ratio
                    val = round(random.uniform(min_v, actual_max), 1)
                    dynamic_options[f"prefix_{stat1}"] = val

        if suffix_id:
            suffix_data = next((s for s in suffixes if s.get("suffix") == suffix_id and s.get("equipment_type") == slot_type), None)
            if suffix_data:
                stat1 = suffix_data.get("stat_1", "")
                if stat1 and stat1 != "-":
                    min_v = float(suffix_data.get("min_stat_1", 0))
                    max_v = float(suffix_data.get("max_stat_1", 0))
                    ilvl_ratio = min(1.0, mlvl / 50.0)
                    actual_max = min_v + (max_v - min_v) * ilvl_ratio
                    val = round(random.uniform(min_v, actual_max), 1)
                    dynamic_options[f"suffix_{stat1}"] = val

        # 5. 아이템 점수 계산
        score = mlvl * 10 + sum(dynamic_options.values()) * 2
        rarity_score_mult = {"magic": 1.0, "rare": 1.5, "craft": 2.0, "unique": 3.0}
        score = int(score * rarity_score_mult.get(rarity, 1.0))

        return {
            "item_uid": str(uuid.uuid4()),
            "base_item_id": base.get("item_idx", ""),
            "item_level": mlvl,
            "rarity": rarity,
            "item_score": score,
            "prefix_id": prefix_id,
            "suffix_id": suffix_id,
            "set_id": prefix_id,  # 세트 = 접두 죄종
            "dynamic_options": dynamic_options,
            "equip_slot": remap_slot(base.get("main_group", "")),
            # 클라이언트 표시용
            "item_name": base.get("item_base", ""),
            "main_group": base.get("main_group", ""),
            "sub_group": base.get("sub_group", ""),
            "min_damage": int(base.get("min_damage", 0)),
            "max_damage": int(base.get("max_damage", 0)),
            "base_defense": int(base.get("base_defense", 0)),
        }
