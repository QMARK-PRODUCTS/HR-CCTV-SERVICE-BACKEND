from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict

class PeopleModel(SQLModel, table=True):
    
    __tablename__ = "people_model"
    
    id: int = Field(primary_key=True)
    role: str = Field(max_length=50, unique=True)
    otherDetails: Dict = Field(sa_column=Column(JSON))
    
    
class People(SQLModel, table=True):
    
    __tablename__ = "people"
    
    id: int = Field(primary_key=True)
    name: str = Field(max_length=50)
    role: str = Field(max_length=50)
    imageUrl: str = Field(max_length=255)
    otherDetails: Dict = Field(sa_column=Column(JSON))
    
    people_model_id: int = Field(default=None, foreign_key="people_model.id")
    
    
    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, role={self.role}, otherDetails={self.otherDetails},people_model_id={self.people_model_id}, user_model={self.people_model})"
    
    def __str__(self):
        return f"User(id={self.id}, name={self.name}, role={self.role}, otherDetails={self.otherDetails}, people_model_id={self.people_model_id}, user_model={self.people_model})"
    
    def __eq__(self, other):
        if not isinstance(other, People):
            return False
        return self.id == other.id and self.name == other.name and self.role == other.role and self.otherDetails == other.otherDetails and self.people_model_id == other.people_model_id and self.people_model == other.people_model