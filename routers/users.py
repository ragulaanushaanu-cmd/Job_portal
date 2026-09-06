from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

import models
from auth import get_current_user, get_admin_user
from dependencies import get_db
from schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserRoleUpdate,
    PasswordChange,
    MessageResponse,
)
from services import user_service


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# ============================================================
# ADMIN - GET ALL USERS
# ============================================================

@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List users",
    description="Returns all users. Administrator access is required.",
    responses={
        403: {"description": "Administrator access required"},
    },
)
def get_users(
    current_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return user_service.get_users(db=db)


# ============================================================
# CURRENT USER
# ============================================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns the currently authenticated user's information.",
    responses={
        401: {"description": "Authentication required"},
    },
)
def get_me(
    current_user: models.User = Depends(get_current_user),
):
    return current_user


# ============================================================
# GET USER
# ============================================================

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user",
    description=(
        "Returns a user's information according to the authenticated "
        "user's permissions."
    ),
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Access denied"},
        404: {"description": "User not found"},
    },
)
def get_user(
    user_id: int = Path(..., ge=1),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.get_user(
        db=db,
        user_id=user_id,
        current_user=current_user,
    )


# ============================================================
# CREATE USER
# ============================================================

@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    description="Creates a new user account with the default Candidate role.",
    responses={
        409: {"description": "User already exists"},
    },
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    return user_service.create_user(
        db=db,
        user_data=user,
    )


# ============================================================
# ADMIN - UPDATE USER ROLE
# ============================================================

@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role",
    description="Updates a user's role. Administrator access is required.",
    responses={
        403: {"description": "Administrator access required"},
        404: {"description": "User not found"},
    },
)
def update_user_role(
    role_data: UserRoleUpdate,
    user_id: int = Path(..., ge=1),
    current_user: models.User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    return user_service.update_user_role(
        db=db,
        user_id=user_id,
        role_data=role_data,
        current_user=current_user,
    )


# ============================================================
# UPDATE USER
# ============================================================

@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user",
    description="Updates user information according to the authenticated user's permissions.",
    responses={
        403: {"description": "Access denied"},
        404: {"description": "User not found"},
        409: {"description": "User data conflicts with an existing user"},
    },
)
def update_user(
    user: UserUpdate,
    user_id: int = Path(..., ge=1),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.update_user(
        db=db,
        user_id=user_id,
        user_data=user,
        current_user=current_user,
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

@router.put(
    "/{user_id}/password",
    response_model=MessageResponse,
    summary="Change user password",
    description="Changes a user's password after validating the current password.",
    responses={
        400: {"description": "Invalid current password or password data"},
        403: {"description": "Access denied"},
        404: {"description": "User not found"},
    },
)
def change_password(
    password_data: PasswordChange,
    user_id: int = Path(..., ge=1),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.change_password(
        db=db,
        user_id=user_id,
        password_data=password_data,
        current_user=current_user,
    )


# ============================================================
# DELETE USER
# ============================================================

@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete a user",
    description="Deletes a user according to the authenticated user's permissions.",
    responses={
        403: {"description": "Access denied"},
        404: {"description": "User not found"},
    },
)
def delete_user(
    user_id: int = Path(..., ge=1),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return user_service.delete_user(
        db=db,
        user_id=user_id,
        current_user=current_user,
    )