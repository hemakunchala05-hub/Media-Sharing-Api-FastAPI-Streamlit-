from pydantic import BaseModel

from fastapi_users import schemas
import uuid
class Post(BaseModel):
    title: str
    content: str
class Postresponse(BaseModel):
    id: int
    title: str
    content: str
    user_id: str
    is_owner: bool

class UserRead(schemas.BaseUser[uuid.UUID]):
    pass    
class UserCreate(schemas.BaseUserCreate):
    pass
class UserUpdate(schemas.BaseUserUpdate):
    pass