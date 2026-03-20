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
# 2. UserStat 테이블 (5스탯: str/int/agi/vit/will)
# ==========================================
class UserStat(Base):
    __tablename__ = "user_stats"

    user_no = Column(Integer, ForeignKey("users.user_no"), primary_key=True)

    # 성장 데이터
    level = Column(Integer, default=1)
    exp = Column(BigInteger, default=0)

    # 순수 스탯 5종 (TheSevenTactics)
    stat_str = Column(Integer, default=5)    # 힘 — 물리 공격력
    stat_int = Column(Integer, default=5)    # 지능 — 마법 공격력, 마나
    stat_agi = Column(Integer, default=5)    # 민첩 — 행동력, 명중, 회피
    stat_vit = Column(Integer, default=5)    # 체력 — HP, 물리 방어
    stat_will = Column(Integer, default=5)   # 의지 — 용병 보정, 죄악 저항
    stat_points = Column(Integer, default=0)

    # 관계 설정
    user = relationship("User", back_populates="stat")

# ==========================================
# 3. Item 테이블 (장비 아이템 — 3부위: weapon/armor/accessory)
# ==========================================
class Item(Base):
    __tablename__ = "items"

    item_uid = Column(String(36), primary_key=True)
    user_no = Column(Integer, ForeignKey("users.user_no"), index=True)

    base_item_id = Column(String(50), nullable=False)
    item_level = Column(Integer, default=1)
    rarity = Column(String(20), default="common")
    item_score = Column(Integer, default=0)
    prefix_id = Column(String(50), nullable=True)
    suffix_id = Column(String(50), nullable=True)
    set_id = Column(String(50), nullable=True)
    dynamic_options = Column(JSON, nullable=True)
    is_equipped = Column(Boolean, default=False, index=True)
    equip_slot = Column(String(20), nullable=True)  # weapon/armor/accessory
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
