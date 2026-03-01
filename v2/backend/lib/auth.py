"""
Authentication utilities for Sasha AI v2
"""

import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from .database import User

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-fallback-change-before-going-public")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username if username else None
    except JWTError:
        return None


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, name: str, password: str, is_admin: bool = False) -> User:
    db_user = User(
        username=username,
        name=name,
        hashed_password=hash_password(password),
        is_admin=is_admin,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_password(db: Session, username: str, new_password: str) -> bool:
    user = get_user_by_username(db, username)
    if not user:
        return False
    user.hashed_password = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    return True


def update_user_theme(db: Session, username: str, theme: str) -> bool:
    user = get_user_by_username(db, username)
    if not user:
        return False
    user.theme_preference = theme
    user.updated_at = datetime.utcnow()
    db.commit()
    return True


def create_default_admin(db: Session):
    admin_user = get_user_by_username(db, "admin")
    if not admin_user:
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        create_user(db, "admin", "Administrator", admin_password, is_admin=True)
        env_set = bool(os.getenv("ADMIN_PASSWORD"))
        print(
            f"Default admin user created: username='admin', "
            f"password={'(from ADMIN_PASSWORD env var)' if env_set else 'admin123 (default — set ADMIN_PASSWORD env var)'}"
        )
        print("Please change the default password after first login!")
