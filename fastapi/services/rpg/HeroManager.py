import logging
from database import SessionLocal
from models import User, Hero
from services.system.GameDataManager import GameDataManager
from services.system.ErrorCode import ErrorCode, error_response

logger = logging.getLogger("RPG_SERVER")

# 스킬트리 포인트 투자당 스킬포인트 소모
SKILL_POINT_COST = 1


class HeroManager:
    """영웅 조회 / 스킬트리 투자 (API 4xxx)"""

    @classmethod
    async def get_heroes(cls, user_no: int, data: dict):
        """API 4001: 보유 영웅 목록 조회"""
        db = SessionLocal()
        try:
            heroes = db.query(Hero).filter(Hero.user_no == user_no).all()

            hero_list = []
            for h in heroes:
                hero_base = cls._get_hero_base(h.hero_id)
                hero_list.append({
                    "hero_uid": h.hero_uid,
                    "hero_id": h.hero_id,
                    "hero_name": hero_base.get("hero_name", h.hero_id) if hero_base else h.hero_id,
                    "grade": h.grade,
                    "faction": h.faction,
                    "level": h.level,
                    "exp": h.exp,
                    "skill_tree_1": h.skill_tree_1,
                    "skill_tree_2": h.skill_tree_2,
                    "tree1_points": h.tree1_points or {},
                    "tree2_points": h.tree2_points or {},
                    "passive_id": h.passive_id,
                    "active_id": h.active_id,
                })

            return {
                "success": True,
                "message": f"영웅 {len(hero_list)}체 조회",
                "data": {"heroes": hero_list},
            }
        except Exception as e:
            logger.error(f"[HeroManager] get_heroes 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "영웅 조회 중 오류가 발생했습니다.")
        finally:
            db.close()

    @classmethod
    async def get_hero_detail(cls, user_no: int, data: dict):
        """API 4002: 영웅 상세 정보"""
        hero_uid = data.get("hero_uid")
        if not hero_uid:
            return error_response(ErrorCode.INVALID_REQUEST, "hero_uid가 필요합니다.")

        db = SessionLocal()
        try:
            hero = db.query(Hero).filter(
                Hero.hero_uid == hero_uid,
                Hero.user_no == user_no
            ).first()

            if not hero:
                return error_response(ErrorCode.ITEM_NOT_FOUND, "영웅을 찾을 수 없습니다.")

            hero_base = cls._get_hero_base(hero.hero_id)
            skill_trees = cls._get_skill_tree_data(hero.skill_tree_1, hero.skill_tree_2)

            return {
                "success": True,
                "message": "영웅 상세 조회",
                "data": {
                    "hero_uid": hero.hero_uid,
                    "hero_id": hero.hero_id,
                    "hero_name": hero_base.get("hero_name", hero.hero_id) if hero_base else hero.hero_id,
                    "grade": hero.grade,
                    "faction": hero.faction,
                    "level": hero.level,
                    "exp": hero.exp,
                    "base_stats": {
                        "str": int(hero_base.get("base_str", 10)) if hero_base else 10,
                        "dex": int(hero_base.get("base_dex", 10)) if hero_base else 10,
                        "vit": int(hero_base.get("base_vit", 10)) if hero_base else 10,
                        "lck": int(hero_base.get("base_lck", 10)) if hero_base else 10,
                        "int": int(hero_base.get("base_int", 10)) if hero_base else 10,
                    },
                    "skill_tree_1": hero.skill_tree_1,
                    "skill_tree_2": hero.skill_tree_2,
                    "tree1_points": hero.tree1_points or {},
                    "tree2_points": hero.tree2_points or {},
                    "skill_trees": skill_trees,
                    "passive_id": hero.passive_id,
                    "passive_name": hero_base.get("passive_name", "") if hero_base else "",
                    "passive_desc": hero_base.get("passive_desc", "") if hero_base else "",
                    "active_id": hero.active_id,
                    "active_name": hero_base.get("active_name", "") if hero_base else "",
                    "active_desc": hero_base.get("active_desc", "") if hero_base else "",
                },
            }
        except Exception as e:
            logger.error(f"[HeroManager] get_hero_detail 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "영웅 상세 조회 중 오류가 발생했습니다.")
        finally:
            db.close()

    @classmethod
    async def invest_skill_point(cls, user_no: int, data: dict):
        """API 4003: 스킬트리 포인트 투자"""
        hero_uid = data.get("hero_uid")
        tree_num = data.get("tree_num")  # 1 or 2
        skill_id = data.get("skill_id")

        if not hero_uid or tree_num not in (1, 2) or not skill_id:
            return error_response(ErrorCode.INVALID_REQUEST, "hero_uid, tree_num(1|2), skill_id가 필요합니다.")

        db = SessionLocal()
        try:
            hero = db.query(Hero).filter(
                Hero.hero_uid == hero_uid,
                Hero.user_no == user_no
            ).with_for_update().first()

            if not hero:
                return error_response(ErrorCode.ITEM_NOT_FOUND, "영웅을 찾을 수 없습니다.")

            # 스킬 트리 유효성 확인
            tree_id = hero.skill_tree_1 if tree_num == 1 else hero.skill_tree_2
            skill_meta = cls._find_skill_in_tree(tree_id, skill_id)
            if not skill_meta:
                return error_response(ErrorCode.INVALID_REQUEST, f"스킬 {skill_id}이(가) 트리 {tree_id}에 없습니다.")

            # 현재 포인트 확인
            points_dict = dict(hero.tree1_points or {}) if tree_num == 1 else dict(hero.tree2_points or {})
            current_level = points_dict.get(skill_id, 0)
            max_level = int(skill_meta.get("max_level", 5))

            if current_level >= max_level:
                return error_response(ErrorCode.INVALID_REQUEST, f"스킬이 이미 최대 레벨({max_level})입니다.")

            # 총 사용 포인트 계산
            total_used = sum(points_dict.values())
            if tree_num == 1:
                total_used += sum((hero.tree2_points or {}).values())
            else:
                total_used += sum((hero.tree1_points or {}).values())

            available_points = hero.level  # 레벨당 1포인트
            cost = int(skill_meta.get("cost_per_level", 1))
            if total_used + cost > available_points:
                return error_response(ErrorCode.INVALID_REQUEST, f"스킬 포인트가 부족합니다. (잔여: {available_points - total_used})")

            # 투자
            points_dict[skill_id] = current_level + 1
            if tree_num == 1:
                hero.tree1_points = points_dict
            else:
                hero.tree2_points = points_dict

            db.commit()

            logger.info(f"[HeroManager] 스킬 투자 (user={user_no}, hero={hero_uid}, {tree_id}/{skill_id} → Lv{current_level + 1})")

            return {
                "success": True,
                "message": f"{skill_meta.get('skill_name', skill_id)} Lv.{current_level + 1}",
                "data": {
                    "hero_uid": hero.hero_uid,
                    "tree_num": tree_num,
                    "skill_id": skill_id,
                    "new_level": current_level + 1,
                    "tree1_points": hero.tree1_points or {},
                    "tree2_points": hero.tree2_points or {},
                },
            }
        except Exception as e:
            db.rollback()
            logger.error(f"[HeroManager] invest_skill_point 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "스킬 투자 중 오류가 발생했습니다.")
        finally:
            db.close()

    # ── 헬퍼 ──

    @staticmethod
    def _get_hero_base(hero_id: str):
        heroes = GameDataManager.REQUIRE_CONFIGS.get("hero_bases", {})
        return heroes.get(hero_id)

    @staticmethod
    def _get_skill_tree_data(tree1_id: str, tree2_id: str) -> dict:
        all_skills = GameDataManager.REQUIRE_CONFIGS.get("skill_trees", {})
        return {
            "tree1": all_skills.get(tree1_id, []),
            "tree2": all_skills.get(tree2_id, []),
        }

    @staticmethod
    def _find_skill_in_tree(tree_id: str, skill_id: str):
        all_skills = GameDataManager.REQUIRE_CONFIGS.get("skill_trees", {})
        for skill in all_skills.get(tree_id, []):
            if skill.get("skill_id") == skill_id:
                return skill
        return None
