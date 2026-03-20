import logging
from database import SessionLocal
from models import Item, Hero
from services.system.GameDataManager import GameDataManager
from services.system.ErrorCode import ErrorCode, error_response

logger = logging.getLogger("RPG_SERVER")

EQUIP_SLOTS = {"weapon", "armor", "accessory"}


class EquipmentManager:
    """장비 인벤토리 / 장착·해제 (API 2xxx)"""

    @classmethod
    async def get_inventory(cls, user_no: int, data: dict):
        """API 2001: 인벤토리 조회 (전체 아이템 + 장착 상태)"""
        db = SessionLocal()
        try:
            items = db.query(Item).filter(Item.user_no == user_no).all()
            equip_map = GameDataManager.REQUIRE_CONFIGS.get("equip_base_map", {})

            item_list = []
            for it in items:
                base = equip_map.get(it.base_item_id, {})
                item_list.append({
                    "item_uid": it.item_uid,
                    "base_item_id": it.base_item_id,
                    "equip_name": base.get("equip_name", it.base_item_id),
                    "equip_slot": it.equip_slot or base.get("equip_slot", ""),
                    "base_stat": base.get("base_stat", ""),
                    "base_value": int(base.get("base_value", 0)),
                    "item_level": it.item_level,
                    "rarity": it.rarity,
                    "is_equipped": it.is_equipped,
                    "equipped_hero_uid": it.equipped_hero_uid,
                    "dynamic_options": it.dynamic_options or {},
                })

            return {
                "success": True,
                "message": f"아이템 {len(item_list)}개 조회",
                "data": {"items": item_list},
            }
        except Exception as e:
            logger.error(f"[EquipmentManager] get_inventory 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "인벤토리 조회 중 오류가 발생했습니다.")
        finally:
            db.close()

    @classmethod
    async def equip_item(cls, user_no: int, data: dict):
        """API 2002: 영웅에게 장비 장착"""
        item_uid = data.get("item_uid")
        hero_uid = data.get("hero_uid")
        if not item_uid or not hero_uid:
            return error_response(ErrorCode.INVALID_REQUEST, "item_uid, hero_uid가 필요합니다.")

        db = SessionLocal()
        try:
            item = db.query(Item).filter(
                Item.item_uid == item_uid,
                Item.user_no == user_no
            ).with_for_update().first()
            if not item:
                return error_response(ErrorCode.ITEM_NOT_FOUND, "아이템을 찾을 수 없습니다.")

            hero = db.query(Hero).filter(
                Hero.hero_uid == hero_uid,
                Hero.user_no == user_no
            ).first()
            if not hero:
                return error_response(ErrorCode.HERO_NOT_FOUND, "영웅을 찾을 수 없습니다.")

            # 장비 슬롯 확인
            equip_map = GameDataManager.REQUIRE_CONFIGS.get("equip_base_map", {})
            base = equip_map.get(item.base_item_id, {})
            slot = base.get("equip_slot", item.equip_slot or "")
            if slot not in EQUIP_SLOTS:
                return error_response(ErrorCode.EQUIP_SLOT_MISMATCH, f"장착 불가 슬롯: {slot}")

            # 해당 영웅의 같은 슬롯에 이미 장착된 아이템 해제
            old_item = db.query(Item).filter(
                Item.user_no == user_no,
                Item.equipped_hero_uid == hero_uid,
                Item.equip_slot == slot,
                Item.is_equipped == True,
            ).with_for_update().first()
            if old_item:
                old_item.is_equipped = False
                old_item.equipped_hero_uid = None

            # 이미 다른 영웅에 장착 중이면 해제
            if item.is_equipped:
                item.is_equipped = False
                item.equipped_hero_uid = None

            # 장착
            item.equip_slot = slot
            item.is_equipped = True
            item.equipped_hero_uid = hero_uid
            db.commit()

            logger.info(f"[EquipmentManager] 장착 (user={user_no}, item={item_uid}, hero={hero_uid}, slot={slot})")

            return {
                "success": True,
                "message": f"{base.get('equip_name', item_uid)} 장착 완료",
                "data": {
                    "item_uid": item_uid,
                    "hero_uid": hero_uid,
                    "equip_slot": slot,
                },
            }
        except Exception as e:
            db.rollback()
            logger.error(f"[EquipmentManager] equip_item 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "장비 장착 중 오류가 발생했습니다.")
        finally:
            db.close()

    @classmethod
    async def unequip_item(cls, user_no: int, data: dict):
        """API 2003: 장비 해제"""
        item_uid = data.get("item_uid")
        if not item_uid:
            return error_response(ErrorCode.INVALID_REQUEST, "item_uid가 필요합니다.")

        db = SessionLocal()
        try:
            item = db.query(Item).filter(
                Item.item_uid == item_uid,
                Item.user_no == user_no
            ).with_for_update().first()
            if not item:
                return error_response(ErrorCode.ITEM_NOT_FOUND, "아이템을 찾을 수 없습니다.")

            if not item.is_equipped:
                return error_response(ErrorCode.INVALID_REQUEST, "장착되어 있지 않은 아이템입니다.")

            equip_map = GameDataManager.REQUIRE_CONFIGS.get("equip_base_map", {})
            base = equip_map.get(item.base_item_id, {})

            item.is_equipped = False
            item.equipped_hero_uid = None
            db.commit()

            logger.info(f"[EquipmentManager] 해제 (user={user_no}, item={item_uid})")

            return {
                "success": True,
                "message": f"{base.get('equip_name', item_uid)} 해제 완료",
                "data": {"item_uid": item_uid},
            }
        except Exception as e:
            db.rollback()
            logger.error(f"[EquipmentManager] unequip_item 실패: {e}", exc_info=True)
            return error_response(ErrorCode.DB_ERROR, "장비 해제 중 오류가 발생했습니다.")
        finally:
            db.close()
