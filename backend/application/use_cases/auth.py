from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from infrastructure.config import AppConfig

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate plain_password to 72 bytes before checking to avoid bcrypt limits
    password_bytes = plain_password.encode('utf-8')[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    # Truncate password to 72 bytes before hashing to avoid bcrypt limits
    password_bytes = password.encode('utf-8')[:72]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, config: AppConfig) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.auth.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.auth.secret_key, algorithm=config.auth.algorithm)
    return encoded_jwt

def decode_access_token(token: str, config: AppConfig) -> dict:
    try:
        payload = jwt.decode(token, config.auth.secret_key, algorithms=[config.auth.algorithm])
        return payload
    except JWTError:
        return None
