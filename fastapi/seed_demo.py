"""
데모 플레이 시드 스크립트
실행: cd fastapi && python seed_demo.py

생성:
- 유저 "demo" (pw: 1234)
- 바알(본캐) + 사탄 + 밴시 영웅
- 3인 파티 편성
- 골드 50000
- 장비 3개 지급
"""
import bcrypt
import uuid
from database import SessionLocal, init_db
from models import User, UserStat, Hero, Party, Item

def seed():
    init_db()
    db = SessionLocal()

    try:
        # 이미 존재하면 스킵
        existing = db.query(User).filter(User.user_name == "demo").first()
        if existing:
            print(f"[SKIP] 'demo' 유저 이미 존재 (user_no={existing.user_no})")
            print(f"  gold={existing.gold}, stage={existing.current_stage}")
            heroes = db.query(Hero).filter(Hero.user_no == existing.user_no).all()
            print(f"  영웅: {[h.hero_id for h in heroes]}")
            return

        # 1. 유저 생성
        pw_hash = bcrypt.hashpw("1234".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(user_name="demo", password_hash=pw_hash, gold=50000, current_stage=101)
        db.add(user)
        db.flush()
        print(f"[OK] 유저 생성: demo (user_no={user.user_no})")

        # 2. 스탯 생성
        stat = UserStat(
            user_no=user.user_no,
            level=5, exp=0,
            stat_str=15, stat_dex=12, stat_vit=12, stat_lck=10, stat_int=11,
            stat_points=10,
        )
        db.add(stat)
        print(f"[OK] 스탯 생성: Lv5, STR15/DEX12/VIT12/LCK10/INT11")

        # 3. 영웅 생성
        baal = Hero(
            user_no=user.user_no, hero_id="baal",
            grade="legendary", faction="demon",
            skill_tree_1="wrath", skill_tree_2="pride",
            tree1_points={"wrath_1": 2, "wrath_3": 1}, tree2_points={},
            passive_id="passive_baal", active_id="active_baal",
            level=5, exp=0,
        )
        db.add(baal)
        db.flush()
        print(f"[OK] 바알 생성 (hero_uid={baal.hero_uid})")

        satan = Hero(
            user_no=user.user_no, hero_id="satan",
            grade="rare", faction="demon",
            skill_tree_1="wrath", skill_tree_2="gluttony",
            tree1_points={"wrath_1": 1}, tree2_points={},
            passive_id="passive_satan", active_id="active_satan",
            level=3, exp=0,
        )
        db.add(satan)
        db.flush()
        print(f"[OK] 사탄 생성 (hero_uid={satan.hero_uid})")

        banshee = Hero(
            user_no=user.user_no, hero_id="banshee",
            grade="uncommon", faction="human",
            skill_tree_1="envy", skill_tree_2="sloth",
            tree1_points={}, tree2_points={"sloth_3": 1},
            passive_id="passive_banshee", active_id="active_banshee",
            level=3, exp=0,
        )
        db.add(banshee)
        db.flush()
        print(f"[OK] 밴시 생성 (hero_uid={banshee.hero_uid})")

        # 4. 파티 편성
        party = Party(
            user_no=user.user_no,
            slot_1=baal.hero_uid,
            slot_2=satan.hero_uid,
            slot_3=banshee.hero_uid,
        )
        db.add(party)
        print(f"[OK] 파티 편성: 바알 / 사탄 / 밴시")

        # 5. 장비 지급 (5부위: weapon/armor/helmet/gloves/boots)
        equips = [
            ("100102", "weapon", baal.hero_uid, "magic"),    # Scimitar (한손검 중형)
            ("200101", "armor", baal.hero_uid, "magic"),     # Dusk Shroud (중갑 소형)
            ("300101", "helmet", baal.hero_uid, "magic"),    # Cap (생존 투구)
            ("400101", "gloves", baal.hero_uid, "magic"),    # Leather Gloves
            ("500101", "boots", baal.hero_uid, "magic"),     # Boots
            ("100301", "weapon", satan.hero_uid, "magic"),   # Tomahawk (도끼 소형)
            ("200201", "armor", satan.hero_uid, "magic"),    # Ghost Armor (경갑)
        ]
        for eid, slot, huid, rarity in equips:
            item = Item(
                item_uid=str(uuid.uuid4()),
                user_no=user.user_no,
                base_item_id=eid,
                item_level=3,
                rarity=rarity,
                equip_slot=slot,
                is_equipped=True,
                equipped_hero_uid=huid,
            )
            db.add(item)
        print(f"[OK] 장비 7개 지급 (바알 5부위 + 사탄 무기/갑옷)")

        db.commit()
        print("\n=== 데모 시드 완료 ===")
        print("로그인: demo / 1234")
        print("골드: 50,000G")
        print("파티: 바알(Lv5) + 사탄(Lv3) + 밴시(Lv3)")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
