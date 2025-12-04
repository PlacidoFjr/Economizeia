from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from argon2 import PasswordHasher
from app.core.config import settings

# Argon2id for password hashing
ph = PasswordHasher()

# JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using Argon2id."""
    return ph.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_reset_token(data: dict) -> str:
    """Create a password reset token (expires in 1 hour)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire, "type": "reset"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24  # Token de verificação expira em 24 horas

def create_verification_token(data: dict) -> str:
    """Create a JWT token for email verification."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire, "type": "verification"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def mask_cpf_cnpj(text: str) -> str:
    """Mask CPF/CNPJ in text for privacy."""
    import re
    # CPF: XXX.XXX.XXX-XX -> XXX.***.***-**
    text = re.sub(r'(\d{3})\.(\d{3})\.(\d{3})-(\d{2})', r'\1.***.***-**', text)
    # CNPJ: XX.XXX.XXX/XXXX-XX -> XX.***.***/****-**
    text = re.sub(r'(\d{2})\.(\d{3})\.(\d{3})/(\d{4})-(\d{2})', r'\1.***.***/****-**', text)
    return text

