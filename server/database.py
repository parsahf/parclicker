from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime


DATABASE_URL = "sqlite:///C:/parcliker/parclicker.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()


# =========================
# LICENSE
# =========================

class License(Base):

    __tablename__ = "licenses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    license_key = Column(
        String,
        unique=True,
        index=True
    )

    username = Column(
        String,
        nullable=True
    )

    active = Column(
        Boolean,
        default=True
    )

    expires_at = Column(
        DateTime,
        nullable=True
    )


# =========================
# USERS
# =========================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        index=True
    )

    password_hash = Column(
        String
    )


# =========================
# SESSIONS
# =========================

class Session(Base):

    __tablename__ = "sessions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    token = Column(
        String,
        unique=True,
        index=True
    )

    username = Column(
        String
    )

    expires_at = Column(
        DateTime
    )


# =========================
# SUBSCRIPTIONS
# =========================

class Subscription(Base):

    __tablename__ = "subscriptions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        index=True
    )

    license_key = Column(
        String,
        unique=True,
        index=True
    )

    # اشتراک برای کدام نرم افزار است
    software_id = Column(
        String,
        index=True,
        nullable=True
    )

    cps = Column(
        Integer
    )

    months = Column(
        Integer
    )

    price = Column(
        Integer
    )

    active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )

    expires_at = Column(
        DateTime,
        nullable=True
    )


# =========================
# SOFTWARE DEVICES
# =========================

class SoftwareDevice(Base):

    __tablename__ = "software_devices"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    software_id = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    username = Column(
        String,
        index=True,
        nullable=True
    )

    active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )


# =========================
# ORDERS
# =========================

class Order(Base):

    __tablename__ = "orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        index=True,
        nullable=False
    )

    software_id = Column(
        String,
        index=True,
        nullable=False
    )

    cps = Column(
        Integer,
        nullable=False
    )

    months = Column(
        Integer,
        nullable=False
    )

    price = Column(
        Integer,
        nullable=False
    )

    status = Column(
        String,
        default="pending"
    )

    created_at = Column(
        DateTime,
        default=datetime.now
    )

    paid_at = Column(
        DateTime,
        nullable=True
    )


# =========================
# CREATE TABLES
# =========================

Base.metadata.create_all(
    bind=engine
)