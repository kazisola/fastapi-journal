from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from schema import UserCreate, UserUpdate, UserPublic, UserPrivate, Token, ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest
from sqlalchemy import select, func, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import models
from datetime import timedelta, datetime, UTC
from email_utils import send_password_reset_email
from config import settings
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    CurrentUser,
    generate_password_reset_token,
    hash_password_reset_token
)
from image_process_utils import process_profile_pic, delete_profile_pic
from PIL import UnidentifiedImageError
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()


# Create a user
@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def user_create(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.username) == user.username.lower()
        )
    )
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists!"
        )

    result = await db.execute(
        select(models.User).where(func.lower(models.User.email) == user.email.lower())
    )
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already exists!",
        )

    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        password_hash=hash_password(user.password),
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


# Login for access token
@router.post("/token", response_model=Token)
async def get_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == form_data.username.lower()
        )
    )
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


# Forgot password
@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(models.User)
        .where(
            func.lower(models.User.email) == request_data.email.lower()
        )
    )
    user = result.scalars().first()

    # If user exists then delete whatever the existing reset tokens they have
    if user:
        await db.execute(
            sql_delete(models.PasswordResetToken)
            .where(
                models.PasswordResetToken.user_id == user.id
            )
        )

        token = generate_password_reset_token()
        token_hash = hash_password_reset_token(token)

        expires_at = datetime.now(UTC) + timedelta(minutes=settings.reset_token_expire_minutes)

        reset_token = models.PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )

        db.add(reset_token)
        await db.commit()

        background_tasks.add_task(
            send_password_reset_email,
            to_email=user.email,
            username=user.username,
            token=token
        )

        return {
            "message": "If an account is found associated with this email, you will get an password reset link."
        }


# Reset password
@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
        reset_data: ResetPasswordRequest,
        db: Annotated[AsyncSession, Depends(get_db)]
    ):
    token_hash = hash_password_reset_token(reset_data.token);
    result = await db.execute(
        select(models.PasswordResetToken)
        .where(models.PasswordResetToken.token_hash == token_hash)
    )
    reset_token = result.scalars().first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    if reset_token.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
        await db.delete(reset_token)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    result = await db.execute(
        select(models.User)
        .where(models.User.id == reset_token.user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user.password_hash = hash_password(reset_data.new_password)

    await db.execute(
        sql_delete(models.PasswordResetToken)
        .where(models.PasswordResetToken.user_id == user.id)
    )
    await db.commit()

    return {
        "message": "Password reset successfully! Please login with your new password."
    }


# Change password
@router.post("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
    ):
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect password"
        )

    current_user.password_hash = hash_password(password_data.new_password)

    await db.execute(
        sql_delete(models.PasswordResetToken)
        .where(models.PasswordResetToken.user_id == current_user.id)
    )
    await db.commit()

    return {
        "message": "Password has been changed successfully!"
    }
    


# Get the logged in user
@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user


# Get a user
@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found!"
        )

    return user


# User update
@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user",
        )

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if (
        user_data.username is not None
        and user_data.username.lower() != user.username.lower()
    ):
        result = await db.execute(
            select(models.User).where(
                func.lower(models.User.username) == user_data.username.lower()
            )
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Username already exists!",
            )

    if user_data.email is not None and user_data.email.lower() != user.email.lower():
        result = await db.execute(
            select(models.User).where(
                func.lower(models.User.email) == user_data.email.lower()
            )
        )
        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Email already exists!",
            )

    if user_data.username is not None:
        user.username = user_data.username
    if user_data.email is not None:
        user.email = user_data.email.lower()

    await db.commit()
    await db.refresh(user)

    return user


# Add user profile image
@router.patch("/{user_id}/picture", response_model=UserPrivate)
async def upload_profile_pic(
    user_id: int,
    file: UploadFile,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
    ):
    if current_user.id is not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to perform this action"
        )
    
    content = await file.read()
    print("content:", content)
    if len(content) > settings.profile_pic_max_bytes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Profile pic size cannot be greater than {1024 * 1024} MB"
        )
    
    try:
        new_filename = await run_in_threadpool(process_profile_pic, content)
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Upload a valid image"
        ) from err
    
    old_filename = current_user.image_file
    current_user.image_file = new_filename

    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        delete_profile_pic(old_filename)

    return current_user

# Delete user profile image
@router.delete("/{user_id}/picture", response_model=UserPrivate)
async def delete_user_profile_pic(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
    ):
    if current_user.id is not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to delete this image"
        )
    old_filename = current_user.image_file
    if old_filename is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No image found"
        )
    current_user.image_file = None
    await db.commit()
    await db.refresh(current_user)
    delete_profile_pic(old_filename)
    
    return current_user


# Delete user
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user",
        )

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    
    old_filename = current_user.image_file

    await db.delete(user)
    await db.commit()

    delete_profile_pic(old_filename)