from sqlmodel import SQLModel, Field, Column, JSON
from typing import Optional, Dict

class CameraSources(SQLModel, table=True):
    
    __tablename__ = "camera_sources"
    
    id: int = Field(primary_key=True)
    type: str = Field(max_length=50)
    sourceCredentials: Dict = Field(sa_column=Column(JSON))
    sourceDetails: Dict = Field(sa_column=Column(JSON))