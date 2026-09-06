from datetime import datetime, timedelta, timezone
import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from dependencies import get_db
import models


# =========================
# ENVIRONMENT CONFIG
# =========================
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not configured")

ALGORITHM = os.getenv("ALGORITHM", "HS256").strip()

if not ALGORITHM:
    raise RuntimeError("ALGORITHM is not configured")

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
except ValueError as exc:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be a valid integer"
    ) from exc

if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be greater than 0"
    )
# =========================
# PASSWORD CONFIG
# =========================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# =========================
# JWT / OAUTH2
# =========================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)


# =========================
# PASSWORD FUNCTIONS
# =========================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# =========================
# JWT FUNCTIONS
# =========================

def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire
    })

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# =========================
# CURRENT USER
# =========================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        user_id = int(user_id)

    except (JWTError, TypeError, ValueError):
        raise credentials_exception

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if user is None:
        raise credentials_exception

    return user


# =========================
# EMPLOYER / ADMIN ACCESS
# =========================

def get_employer_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:

    if current_user.role.lower() not in {
        "employer",
        "admin"
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employer access required"
        )

    return current_user


# =========================
# ADMIN ACCESS
# =========================

def get_admin_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:

    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


# =========================
# CANDIDATE ACCESS
# =========================

def get_candidate_user(
    current_user: models.User = Depends(get_current_user)
) -> models.User:

    if current_user.role.lower() != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidate access required"
        )

    return current_user













