from services.system import GameDataManager, UserInitManager, UserInfoManager


class APIManager:
    api_map = {
        # === 시스템 및 로그인 API (1xxx) ===
        1002: (GameDataManager, GameDataManager.get_all_configs),
        1003: (UserInitManager, UserInitManager.create_new_user),
        1004: (UserInfoManager, UserInfoManager.get_user_info),
        1005: (UserInfoManager, UserInfoManager.reset_stats),
        1007: (UserInitManager, UserInitManager.login),
    }
