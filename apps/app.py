from datetime import datetime
import uuid

from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from apps.db import User, get_async_session, create_db_and_tables, Post
from apps.images import get_imagekit
from apps.users import fastapi_users, current_active_user,auth_backend
from apps.schemas import UserRead, UserCreate, UserUpdate   

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),prefix="/auth/jwt", tags=["auth"])
app.include_router(
    fastapi_users.get_register_router(UserRead,UserCreate), prefix="/auth", tags=["auth"])
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])
app.include_router(
    fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])   
app.include_router(
    fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])   

@app.post("/upload")
async def upload_file(
    caption: str = Form(...),
    user: User = Depends(current_active_user),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    try:
        get_imagekit()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    post = Post(
        user_id=user.id,
        caption=caption,
        url=f"/uploads/{file.filename}",
        file_type=file.content_type or "unknown",
        file_name=file.filename,
        created_at=datetime.utcnow(),
    )

    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post


@app.get("/feed")
async def get_feed(user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.fetchall()]
    posts_data = []

    result = await session.execute(select(User).where(User.id.in_([post.user_id for post in posts])))
    users = {user.id: user for user in result.scalars().all()}
    for post in posts:
        posts_data.append(
            {
            "id": post.id,
            "user_id": str(post.user_id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at,
            "is_owner": post.user_id == user.id,
            "email": users[post.user_id].email if post.user_id in users else None
            }
        )

    return {"posts": posts_data}

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, user: User = Depends(current_active_user), session: AsyncSession = Depends(get_async_session)):

    try:
        post_uuid = uuid.UUID(post_id)
        result = await session.execute(select(Post).where(Post.id == post_id))
        post = result.scalar_one_or_none()

        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.user_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this post")
        await session.delete(post)
        await session.commit()
        return {"message": "Post deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))