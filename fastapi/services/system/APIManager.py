from services.system import GameDataManager, UserInitManager, UserInfoManager
from services.rpg import HeroManager, TavernManager, PartyManager, BattleManager


class APIManager:
    api_map = {
        # === 시스템 및 로그인 API (1xxx) ===
        1002: (GameDataManager, GameDataManager.get_all_configs),
        1003: (UserInitManager, UserInitManager.create_new_user),
        1004: (UserInfoManager, UserInfoManager.get_user_info),
        1005: (UserInfoManager, UserInfoManager.reset_stats),
        1007: (UserInitManager, UserInitManager.login),

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
