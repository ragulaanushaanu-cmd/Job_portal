from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from dependencies import get_db
from auth import verify_password, create_access_token
import models


router = APIRouter(
    tags=["Authentication"]
)


@router.post(
    "/login",
    summary="Authenticate a user",
    description=(
        "Authenticates a user using their email address and password "
        "and returns a bearer access token."
    ),
    responses={
        401: {"description": "Invalid email or password"},
    },
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = (
        db.query(models.User)
        .filter(models.User.email == form_data.username)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        form_data.password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }