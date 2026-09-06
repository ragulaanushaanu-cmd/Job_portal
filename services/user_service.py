from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

import models
from auth import hash_password, verify_password
from schemas import PasswordChange, UserRoleUpdate


# ============================================================
# GET ALL USERS
# ============================================================

def get_users(
    db: Session,
):
    return (
        db.query(models.User)
        .order_by(models.User.id.asc())
        .all()
    )


# ============================================================
# GET SINGLE USER
# ============================================================

def get_user(
    db: Session,
    user_id: int,
    current_user: models.User,
):
    is_admin = current_user.role.lower() == "admin"
    is_self = current_user.id == user_id

    if not (is_self or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user",
        )

    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    db: Session,
    user_data,
):
    existing_user = (
        db.query(models.User)
        .filter(models.User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    user_data_dict = user_data.model_dump()

    # Never trust the client to choose the role during
    # normal registration.
    user_data_dict["role"] = "Candidate"

    # Never store passwords in plain text.
    user_data_dict["password"] = hash_password(
        user_data.password
    )

    new_user = models.User(**user_data_dict)

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


# ============================================================
# UPDATE USER
# ============================================================

def update_user(
    db: Session,
    user_id: int,
    user_data,
    current_user: models.User,
):
    target_user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    is_admin = current_user.role.lower() == "admin"
    is_self = current_user.id == user_id

    # User can update their own account.
    # Admin can update another user's account.
    if not (is_self or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )

    update_data = user_data.model_dump(
        exclude_unset=True
    )

    # --------------------------------------------------------
    # EMAIL SECURITY
    # --------------------------------------------------------

    if "email" in update_data:

        new_email = update_data["email"]

        if new_email != target_user.email:

            existing_email = (
                db.query(models.User)
                .filter(
                    models.User.email == new_email,
                    models.User.id != user_id,
                )
                .first()
            )

            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already exists",
                )

    # --------------------------------------------------------
    # PASSWORD
    # --------------------------------------------------------
    #
    # Password is intentionally NOT part of UserUpdate.
    # Password changes must go through /password.
    #
    # --------------------------------------------------------

    # --------------------------------------------------------
    # APPLY CHANGES
    # --------------------------------------------------------

    for key, value in update_data.items():
        setattr(target_user, key, value)

    try:
        db.commit()
        db.refresh(target_user)

        return target_user

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User update violates a database constraint",
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


# ============================================================
# UPDATE USER ROLE - ADMIN ONLY
# ============================================================

def update_user_role(
    db: Session,
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: models.User,
):
    # Only Admin can change user roles.
    if current_user.role.lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin can change user roles",
        )

    target_user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    new_role = role_data.role.value

    # Prevent an Admin from removing their own Admin role.
    if target_user.id == current_user.id and new_role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot remove their own Admin role",
        )

    target_user.role = new_role

    try:
        db.commit()
        db.refresh(target_user)

        return target_user

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user role",
        )


# ============================================================
# CHANGE PASSWORD
# ============================================================

def change_password(
    db: Session,
    user_id: int,
    password_data: PasswordChange,
    current_user: models.User,
):
    # A user can only change their own password.
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password",
        )

    # Verify current password.
    if not verify_password(
        password_data.current_password,
        current_user.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    # Prevent reusing the same password.
    if verify_password(
        password_data.new_password,
        current_user.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the old password",
        )

    current_user.password = hash_password(
        password_data.new_password
    )

    try:
        db.commit()

        return {
            "message": "Password updated successfully"
        }

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password",
        )


# ============================================================
# DELETE USER
# ============================================================

def delete_user(
    db: Session,
    user_id: int,
    current_user: models.User,
):
    target_user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    is_admin = current_user.role.lower() == "admin"
    is_self = current_user.id == user_id

    # User can delete their own account.
    # Admin can delete another user's account.
    if not (is_self or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user",
        )

    # Prevent an Admin from deleting their own Admin account.
    if is_admin and is_self:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot delete their own account",
        )

    try:
        db.delete(target_user)
        db.commit()

        return {
            "message": "User deleted successfully"
        }

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "User cannot be deleted because they own "
                "or are linked to existing records"
            ),
        )

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )