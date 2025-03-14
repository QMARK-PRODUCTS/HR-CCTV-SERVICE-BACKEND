from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field

class Users(SQLModel, table=True):
    
    __tablename__ = "users"
    
    id: int = Field(primary_key=True)
    name: str = Field(max_length=50, nullable=False)
    email: str = Field(max_length=50, nullable=False)
    password: str = Field(nullable=False)
    role: str = Field(max_length=50, default="moderator")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    isActive: Optional[bool] = Field(default=True)
    
    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email}, role={self.role})"
    
    def __str__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email}, role={self.role})"
    
    def __eq__(self, other):
        if not isinstance(other, Users):
            return False
        return self.id == other.id and self.name == other.name and self.email == other.email and self.role == other.role