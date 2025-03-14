from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class UsersGetSchema(BaseModel):
    id: Optional[int] = None
    name: str
    email: str
    role: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    isActive: Optional[bool] = True

    class Config:
        from_attributes = True
        
        
class UserCreateSchema(BaseModel):
    name: str
    email: str
    password: str
    role: str
    isActive: Optional[bool] = True

    class Config:
        from_attributes = True
        
class UserUpdateSchema(BaseModel):
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True
        
        
class UserAuthSchema(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True
        
        
class RefreshTokenSchema(BaseModel):
    refreshToken: str

    class Config:
        from_attributes = True