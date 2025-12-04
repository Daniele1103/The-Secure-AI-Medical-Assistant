from datetime import datetime, timedelta
from passlib.context import CryptContext
from typing import Optional
import jwt
import os

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret")
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_minutes: int = 60):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token scaduto
        return None
    except jwt.InvalidTokenError:
        # Token invalido
        return None

def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Decodifica il JWT e ritorna l'user_id, oppure None se invalido.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_email_from_token(token: str) -> Optional[str]:
    """
    Decodifica il JWT e ritorna la email, oppure None se invalido.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("email")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None