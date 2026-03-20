# models.py — TheSevenTactics
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# ==========================================
# 1. User 테이블 (계정 메타 데이터)
# ==========================================
class User(Base):
    __tablename__ = "users"

    user_no = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, default=func.now(), onupdate=func.now())
    status = Column(String(20), default="ACTIVE")

    gold = Column(BigInteger, default=0)
    current_stage = Column(Integer, default=101)

    # 관계 설정
    stat = relationship("UserStat", back_populates="user", uselist=False, cascade="all, delete-orphan")
    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")
    heroes = relationship("Hero", back_populates="user", cascade="all, delete-orphan")
    party = relationship("Party", back_populates="user", uselist=False, cascade="all, delete-orphan")
    tavern = relationship("Tavern", back_populates="user", uselist=False, cascade="all, delete-orphan")

# ==========================================
# 2. UserStat 테이블 (5스탯: STR/DEX/VIT/LCK/INT)
# ==========================================
class UserStat(Base):
    __tablename__ = "user_stats"

    user_no = Column(Integer, ForeignKey("users.user_no"), primary_key=True)

    # 성장 데이터
    level = Column(Integer, default=1)
    exp = Column(BigInteger, default=0)

    # 순수 스탯 5종 (TheSevenRPG 스탯 체계)
    stat_str = Column(Integer, default=10)    # 힘(STR) — 물리 공격력
    stat_dex = Column(Integer, default=10)    # 민첩(DEX) — 공격속도, 명중, 회피
    stat_vit = Column(Integer, default=10)    # 체력(VIT) — HP, 물리 방어
    stat_lck = Column(Integer, default=10)    # 운(LCK) — 치명타 확률/데미지
    stat_int = Column(Integer, default=10)    # 지능(INT) — 마법 공격력, 스킬 증폭
    stat_points = Column(Integer, default=0)

    # 관계 설정
    user = relationship("User", back_populates="stat")

# ==========================================
# 3. Item 테이블 (장비 아이템 — 5부위: weapon/armor/helmet/gloves/boots)
# ==========================================
class Item(Base):
    __tablename__ = "items"

    item_uid = Column(String(36), primary_key=True)
    user_no = Column(Integer, ForeignKey("users.user_no"), index=True)

    base_item_id = Column(String(50), nullable=False)   # equipment_base.csv item_idx 참조
    item_level = Column(Integer, default=1)              # ilvl = 드롭 몬스터 mlvl
    rarity = Column(String(20), default="magic")         # magic/rare/craft/unique
    item_score = Column(Integer, default=0)
    prefix_id = Column(String(50), nullable=True)        # 7죄종 접두사
    suffix_id = Column(String(50), nullable=True)        # 7죄종 접미사
    set_id = Column(String(50), nullable=True)           # 세트 ID
    dynamic_options = Column(JSON, nullable=True)         # 공통 옵션 + 수치
    is_equipped = Column(Boolean, default=False, index=True)
    equip_slot = Column(String(20), nullable=True)       # weapon/armor/helmet/gloves/boots
    equipped_hero_uid = Column(Integer, ForeignKey("heroes.hero_uid"), nullable=True)

    # 관계 설정
    user = relationship("User", back_populates="items")

# ==========================================
# 4. Hero 테이블 (영웅 보유 정보)
# ==========================================
class Hero(Base):
    __tablename__ = "heroes"

    hero_uid = Column(Integer, primary_key=True, autoincrement=True)
    user_no = Column(Integer, ForeignKey("users.user_no"), index=True, nullable=False)
    hero_id = Column(String(50), nullable=False)         # 영웅 기본 ID (hero_base.csv 참조)
    grade = Column(String(20), default="common")          # common/uncommon/rare/legendary
    faction = Column(String(20), nullable=False)           # human/demon/celestial

    # 성장
    level = Column(Integer, default=1)
    exp = Column(BigInteger, default=0)

    # 스킬트리 — 7죄종 중 2개 보유
    skill_tree_1 = Column(String(20), nullable=False)     # wrath/envy/greed/sloth/gluttony/lust/pride
    skill_tree_2 = Column(String(20), nullable=False)
    tree1_points = Column(JSON, default=dict)              # {"skill_id": level, ...}
    tree2_points = Column(JSON, default=dict)

    # 고유 능력
    passive_id = Column(String(50), nullable=True)        # 고유 패시브 ID
    active_id = Column(String(50), nullable=True)         # 고유 액티브 스킬 ID

    created_at = Column(DateTime, default=func.now())

    # 관계 설정
    user = relationship("User", back_populates="heroes")

# ==========================================
# 5. Party 테이블 (3인 파티 편성)
# ==========================================
class Party(Base):
    __tablename__ = "parties"

    user_no = Column(Integer, ForeignKey("users.user_no"), primary_key=True)
    slot_1 = Column(Integer, nullable=True)    # hero_uid (바알=본캐, 항상 슬롯1)
    slot_2 = Column(Integer, nullable=True)    # hero_uid
    slot_3 = Column(Integer, nullable=True)    # hero_uid

    # 관계 설정
    user = relationship("User", back_populates="party")

# ==========================================
# 6. Tavern 테이블 (선술집 — 방문 영웅 상태)
# ==========================================
class Tavern(Base):
    __tablename__ = "taverns"

    user_no = Column(Integer, ForeignKey("users.user_no"), primary_key=True)
    hero_id = Column(String(50), nullable=True)           # 방문 영웅 ID (없으면 비어있음)
    grade = Column(String(20), nullable=True)
    faction = Column(String(20), nullable=True)
    skill_tree_1 = Column(String(20), nullable=True)
    skill_tree_2 = Column(String(20), nullable=True)
    passive_id = Column(String(50), nullable=True)
    active_id = Column(String(50), nullable=True)
    arrived_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # 관계 설정
    user = relationship("User", back_populates="tavern")
