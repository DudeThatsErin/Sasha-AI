"""
Authentication utilities for Sasha AI
"""

import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from .database import User

# JWT Configuration
SECRET_KEY = "sasha-ai-secret-key-change-in-production"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return username"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by username"""
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, name: str, password: str, is_admin: bool = False) -> User:
    """Create a new user"""
    hashed_password = hash_password(password)
    db_user = User(
        username=username,
        name=name,
        hashed_password=hashed_password,
        is_admin=is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_password(db: Session, username: str, new_password: str) -> bool:
    """Update a user's password"""
    user = get_user_by_username(db, username)
    if not user:
        return False
    
    user.hashed_password = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    return True

def update_user_theme(db: Session, username: str, theme: str) -> bool:
    """Update a user's theme preference"""
    user = get_user_by_username(db, username)
    if not user:
        return False
    
    user.theme_preference = theme
    user.updated_at = datetime.utcnow()
    db.commit()
    return True

def create_default_admin(db: Session):
    """Create default admin user if it doesn't exist"""
    admin_user = get_user_by_username(db, "admin")
    if not admin_user:
        create_user(db, "admin", "Administrator", "admin123", is_admin=True)
        print("Default admin user created: username='admin', name='Administrator', password='admin123'")
        print("Please change the default password after first login!")
