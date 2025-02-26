from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict

class UserModel(SQLModel, table=True):
    
    __tablename__ = "user_model"
    
    id: int = Field(primary_key=True)
    role: str = Field(max_length=50, unique=True)
    otherDetails: Dict = Field(sa_column=Column(JSON))
    
    
class User(SQLModel, table=True):
    
    __tablename__ = "user"
    
    id: int = Field(primary_key=True)
    name: str = Field(max_length=50)
    role: str = Field(max_length=50)
    imageUrl: str = Field(max_length=255)
    otherDetails: Dict = Field(sa_column=Column(JSON))
    
    user_model_id: int = Field(default=None, foreign_key="user_model.id")
    
    
    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, role={self.role}, otherDetails={self.otherDetails}, user_model_id={self.user_model_id}, user_model={self.user_model})"
    
    def __str__(self):
        return f"User(id={self.id}, name={self.name}, role={self.role}, otherDetails={self.otherDetails}, user_model_id={self.user_model_id}, user_model={self.user_model})"
    
    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.id == other.id and self.name == other.name and self.role == other.role and self.otherDetails == other.otherDetails and self.user_model_id == other.user_model_id and self.user_model == other.user_model