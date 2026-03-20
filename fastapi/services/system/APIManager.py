class APIManager:
    api_map = None

    @classmethod
    def _init_map(cls):
        """지연 초기화 — 순환 import 방지"""
        if cls.api_map is not None:
            return
        from services.system.GameDataManager import GameDataManager
        from services.system.UserInitManager import UserInitManager
        from services.system.UserInfoManager import UserInfoManager
        from services.rpg.HeroManager import HeroManager
        from services.rpg.TavernManager import TavernManager
        from services.rpg.PartyManager import PartyManager
        from services.rpg.BattleManager import BattleManager
        from services.rpg.EquipmentManager import EquipmentManager

        cls.api_map = {
            # === 시스템 및 로그인 API (1xxx) ===
            1002: (GameDataManager, GameDataManager.get_all_configs),
            1003: (UserInitManager, UserInitManager.create_new_user),
            1004: (UserInfoManager, UserInfoManager.get_user_info),
            1005: (UserInfoManager, UserInfoManager.reset_stats),
            1007: (UserInitManager, UserInitManager.login),

            # === 인벤토리/장비 API (2xxx) ===
            2001: (EquipmentManager, EquipmentManager.get_inventory),
            2002: (EquipmentManager, EquipmentManager.equip_item),
            2003: (EquipmentManager, EquipmentManager.unequip_item),
            2004: (EquipmentManager, EquipmentManager.sell_item),

            # === 전투 API (3xxx) ===
            3001: (BattleManager, BattleManager.battle_start),

            # === 영웅 API (4xxx) ===
            4001: (HeroManager, HeroManager.get_heroes),
            4002: (HeroManager, HeroManager.get_hero_detail),
            4003: (HeroManager, HeroManager.invest_skill_point),

            # === 선술집 API (5xxx) ===
            5001: (TavernManager, TavernManager.get_tavern),
            5002: (TavernManager, TavernManager.recruit_hero),
            5003: (TavernManager, TavernManager.dismiss_visitor),

            # === 파티 API (6xxx) ===
            6001: (PartyManager, PartyManager.get_party),
            6002: (PartyManager, PartyManager.set_party),
        }
